from ._anvil_designer import ProgressTrackerMobileViewTemplate
from anvil import *
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.server
import anvil.users
import anvil.js
from .. import ModGetData
from ..JobCardForm import JobCardForm
from ..DefectsForm import DefectsForm
from ..QuoteForm import QuoteForm
from ..InvoiceForm import InvoiceForm
from ..PaymentForm import PaymentForm
from ..ConfirmForm import ConfirmForm
from ..VehicleInspectionChecklist import VehicleInspectionChecklist

class ProgressTrackerMobileView(ProgressTrackerMobileViewTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')
        self._rt_tokens = []
        self._rt_conn_token = None
        self._modals_cache = {}
        self._modals_cache_job_id = None
        self._prewarmed_modals = {}
        self._job_bundles_lru = {}
        self._tracker_summary_map = {}
        self._inflight_bundle_jobs = set()
        self._preload_modal_assets()
        self._attach_hover_prewarm()
        if hasattr(self.txtJobCardRef, "set_event_handler"):
            self.txtJobCardRef.set_event_handler("pressed_enter", self.btn_SearchCustomer_click)
        self.set_event_handler("show", self.form_show)
        self.set_event_handler("hide", self.form_hide)
        try:
            anvil.js.window.setTimeout(self._warm_search_index_async, 0)
        except Exception:
            pass

    def _warm_search_index_async(self, _evt=None, force_refresh=False):
        try:
            fn = getattr(ModGetData, "getTrackerSearchIndexCached", None)
            if not callable(fn):
                return
            rows = fn(force_refresh=force_refresh) or []
            smap = getattr(self, "_tracker_summary_map", None)
            if smap is None:
                self._tracker_summary_map = smap = {}
            for entry in rows:
                jid = entry.get("id")
                if jid is not None and "summary" in entry:
                    smap[int(jid) if str(jid).isdigit() else jid] = entry["summary"]
        except Exception:
            pass

    def _preload_modal_assets(self):
        try:
            img_cls = getattr(anvil.js.window, "Image", None)
            if img_cls:
                for asset in ("_/theme/Invoice Header Logo.jpg", "_/theme/screen.png"):
                    img = img_cls()
                    img.src = asset
        except Exception:
            pass

    def _attach_hover_prewarm(self):
        button_map = (
            ("btn_JobCard", "jobcard"),
            ("btn_Defects", "defects"),
            ("btn_Quotation", "quote"),
            ("btn_Confirmed", "confirm"),
            ("btn_Invoice", "invoice"),
            ("btn_Payment", "payment"),
        )
        for attr, key in button_map:
            btn = getattr(self, attr, None)
            if btn is None:
                continue
            try:
                dom_node = anvil.js.get_dom_node(btn)
                def _make_handler(modal_key):
                    def _handler(_evt=None):
                        jid = self.drop_down_JobCardRefDetails.selected_value
                        if jid:
                            self._prewarm_single_modal(jid, modal_key)
                    return _handler
                h = _make_handler(key)
                dom_node.addEventListener("pointerenter", h, {"passive": True})
                dom_node.addEventListener("mousedown", h, {"passive": True})
                dom_node.addEventListener("touchstart", h, {"passive": True})
            except Exception:
                pass
        search_btn = getattr(self, "btn_SearchCustomer", None)
        if search_btn is not None:
            try:
                s_dom = anvil.js.get_dom_node(search_btn)
                s_dom.addEventListener("pointerenter", self._warm_search_index_async, {"passive": True})
                s_dom.addEventListener("mousedown", self._warm_search_index_async, {"passive": True})
                s_dom.addEventListener("touchstart", self._warm_search_index_async, {"passive": True})
            except Exception:
                pass

    def _evict_lru_job(self, job_id=None):
        smap = getattr(self, "_tracker_summary_map", None)
        if smap:
            if job_id is None:
                smap.clear()
            else:
                for k in list(smap.keys()):
                    if str(k) == str(job_id):
                        smap.pop(k, None)
        lru = getattr(self, "_job_bundles_lru", None)
        if not lru:
            return
        if job_id is None:
            lru.clear()
        else:
            for k in list(lru.keys()):
                if str(k) == str(job_id):
                    lru.pop(k, None)

    def _store_lru_job(self, job_id, tracker_data, modals_bundle, prewarmed=None):
        lru = getattr(self, "_job_bundles_lru", None)
        if lru is None:
            self._job_bundles_lru = lru = {}
        lru.pop(job_id, None)
        lru[job_id] = {
            "tracker": tracker_data,
            "modals": modals_bundle,
            "prewarmed": prewarmed if prewarmed is not None else {},
        }
        while len(lru) > 8:
            oldest = next(iter(lru))
            lru.pop(oldest, None)

    def _invalidate_modals_cache(self, job_id=None):
        self._evict_lru_job(job_id)
        if job_id is None or self._modals_cache_job_id == job_id:
            self._modals_cache = {}
            self._modals_cache_job_id = None
            self._prewarmed_modals = {}

    def _build_modal_instance(self, job_id, key, data):
        if not data:
            return None
        if key == "jobcard":
            return JobCardForm(jobcard_data=data, prewarm_edit=False)
        if key == "defects":
            return DefectsForm(job_id=job_id, init_data=data)
        if key == "quote":
            return QuoteForm(job_id, quote_data=data)
        if key == "confirm":
            return ConfirmForm(job_id, quote_data=data)
        if key == "invoice":
            return InvoiceForm(job_id, quote_data=data)
        if key == "payment":
            return PaymentForm(job_id, payment_data=data)
        return None

    def _prewarm_for_bundle(self, job_id, modals_bundle, prewarmed_dict, key):
        if key in prewarmed_dict:
            return
        data = modals_bundle.get(key)
        if not data:
            return
        try:
            inst = self._build_modal_instance(job_id, key, data)
            if inst is not None:
                prewarmed_dict[key] = inst
        except Exception:
            pass

    def _prewarm_single_modal(self, job_id, key):
        if self._modals_cache_job_id != job_id:
            return
        prewarmed = getattr(self, "_prewarmed_modals", None)
        if prewarmed is None:
            self._prewarmed_modals = prewarmed = {}
        self._prewarm_for_bundle(job_id, self._modals_cache, prewarmed, key)

    def _schedule_prewarm_single_modal(self, job_id, key):
        try:
            anvil.js.window.setTimeout(lambda: self._prewarm_single_modal(job_id, key), 0)
        except Exception:
            pass

    def _priority_modal_keys(self, active_status=None):
        status_first = {
            "Checked In": ("jobcard", "defects"),
            "Create Quote": ("defects", "quote", "jobcard"),
            "Confirm Quote": ("quote", "confirm", "defects"),
            "In Service": ("confirm", "defects", "jobcard"),
            "Verify Task": ("defects", "confirm", "jobcard"),
            "Issue Invoice": ("invoice", "confirm", "defects"),
            "Pending": ("payment", "invoice", "jobcard"),
            "Paid": ("payment", "invoice", "jobcard"),
            "Complete": ("invoice", "payment", "jobcard"),
        }.get(active_status, ())
        all_keys = ("jobcard", "defects", "quote", "confirm", "invoice", "payment")
        ordered = list(status_first)
        for k in all_keys:
            if k not in ordered:
                ordered.append(k)
        return tuple(ordered)

    def _schedule_prewarm_modals(self, job_id, active_status=None):
        keys = self._priority_modal_keys(active_status)
        def _step(idx=0):
            if idx >= len(keys):
                return
            if self._modals_cache_job_id != job_id:
                return
            self._prewarm_single_modal(job_id, keys[idx])
            try:
                anvil.js.window.setTimeout(lambda: _step(idx + 1), 0)
            except Exception:
                pass
        try:
            anvil.js.window.setTimeout(lambda: _step(0), 0)
        except Exception:
            pass

    def _pop_or_build_modal(self, job_id, key, data):
        prewarmed = getattr(self, "_prewarmed_modals", None)
        if self._modals_cache_job_id == job_id and prewarmed and key in prewarmed:
            return prewarmed.pop(key)
        return self._build_modal_instance(job_id, key, data)

    def _prefetch_modals(self, job_id):
        if not job_id or self.drop_down_JobCardRefDetails.selected_value != job_id:
            return
        try:
            with anvil.server.no_loading_indicator:
                bundle = anvil.server.call_s("get_progress_tracker_modals_bundle", job_id)
            if bundle and self.drop_down_JobCardRefDetails.selected_value == job_id:
                self._modals_cache = bundle
                self._modals_cache_job_id = job_id
                self._prewarmed_modals = {}
                self._schedule_prewarm_modals(job_id)
        except Exception:
            pass

    def _schedule_prefetch_modals(self, job_id):
        try:
            anvil.js.window.setTimeout(lambda: self._prefetch_modals(job_id), 0)
        except Exception:
            self._prefetch_modals(job_id)

    def _get_cached_or_fetch(self, job_id, key, server_fn):
        if self._modals_cache_job_id == job_id and key in self._modals_cache:
            return self._modals_cache[key]
        data = anvil.server.call(server_fn, job_id)
        if self._modals_cache_job_id != job_id:
            self._modals_cache = {}
            self._modals_cache_job_id = job_id
        self._modals_cache[key] = data
        return data

    def _sync_timer_with_ws(self):
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            ws_live = bool(rt and rt.isConnected())
        except Exception:
            ws_live = False
        if ws_live:
            self.timer_update.interval = 0
            self.timer_update.enabled = False
        else:
            self.timer_update.interval = 60
            self.timer_update.enabled = True

    def _on_realtime_event(self, evt=None):
        entity_id = evt.get("entity_id") if isinstance(evt, dict) else None
        inv_fn = getattr(ModGetData, "invalidateTrackerSearchIndex", None)
        if callable(inv_fn):
            inv_fn()
        self._evict_lru_job(entity_id)
        try:
            anvil.js.window.setTimeout(lambda: self._warm_search_index_async(force_refresh=True), 50)
        except Exception:
            pass
        selected_id = self.drop_down_JobCardRefDetails.selected_value
        if not selected_id:
            return
        if entity_id is None or str(entity_id) == str(selected_id):
            self.refresh_selected_job_card(force_server=True)

    def form_show(self, **event_args):
        self.form_hide()
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                self._rt_tokens = [
                    rt.subscribe("jobcards", self._on_realtime_event),
                    rt.subscribe("payments", self._on_realtime_event),
                    rt.subscribe("contacts", self._on_realtime_event),
                ]
                def _on_conn(status):
                    self._sync_timer_with_ws()
                    if status and status.get("reconnected"):
                        self._evict_lru_job(None)
                        self._warm_search_index_async(force_refresh=True)
                        self.refresh_selected_job_card(force_server=True)
                self._rt_conn_token = rt.onConnectionChange(_on_conn)
        except Exception:
            pass
        self._sync_timer_with_ws()
        if getattr(ModGetData, "peekTrackerSearchIndexCached", lambda: None)() is None:
            try:
                anvil.js.window.setTimeout(self._warm_search_index_async, 0)
            except Exception:
                pass

    def form_hide(self, **event_args):
        self.timer_update.interval = 0
        self.timer_update.enabled = False
        try:
            rt = getattr(anvil.js.window, "bmaRealtime", None)
            if rt:
                for tok in self._rt_tokens:
                    rt.unsubscribe(tok)
                if self._rt_conn_token:
                    rt.offConnectionChange(self._rt_conn_token)
        except Exception:
            pass
        self._rt_tokens = []
        self._rt_conn_token = None

    def timer_update_tick(self, **event_args):
        self.refresh_selected_job_card(force_server=True)

    def _store_modals_into_lru_and_active(self, job_id, modals, summary=None):
        smap = getattr(self, "_tracker_summary_map", None) or {}
        tracker_summary = summary or smap.get(job_id)
        if tracker_summary is None and modals and modals.get("jobcard"):
            jc = modals["jobcard"]
            inv_rows = modals.get("invoice") or []
            pay_rows = modals.get("payment") or []
            raw_inv = sum(
                (r["QuantityIssued"] if isinstance(r.get("QuantityIssued"), (int, float)) else 1.0)
                * (r.get("Amount") or 0.0)
                for r in inv_rows
            )
            raw_pay = sum(
                float(str(r.get("AmountPaid") or 0).replace(",", "") or 0)
                for r in pay_rows
            )
            tracker_summary = {
                "job_card": {
                    "ID": jc["ID"],
                    "ClientDetails": jc["ClientDetails"],
                    "RegNo": jc["RegNo"],
                    "MakeAndModel": jc["MakeAndModel"],
                    "Mileage": jc["Mileage"],
                    "ReceivedDate": jc["ReceivedDate"],
                    "Status": jc["Status"],
                },
                "client": {
                    "Fullname": jc.get("ClientFullname", ""),
                    "Phone": jc.get("ClientPhone", ""),
                },
                "invoice_status": inv_rows[-1].get("Status") if inv_rows else None,
                "invoice_total": f"{float(raw_inv):,.2f}" if inv_rows else 0.0,
                "previous_payment": f"{float(raw_pay):,.2f}" if pay_rows else 0.0,
                "cancelled_reason": "",
            }
        if tracker_summary is None:
            return
        prewarmed = {}
        self._store_lru_job(job_id, tracker_summary, modals, prewarmed)
        if self.drop_down_JobCardRefDetails.selected_value == job_id:
            self._modals_cache = modals
            self._modals_cache_job_id = job_id
            self._prewarmed_modals = prewarmed
            jc_status = tracker_summary["job_card"]["Status"]
            eff = tracker_summary["invoice_status"] if jc_status == "Ready for Pickup" else jc_status
            self._schedule_prewarm_modals(job_id, active_status=eff)
            return

        keys = ("jobcard", "defects", "quote", "confirm", "invoice", "payment")
        def _bg_step(idx=0):
            if idx >= len(keys):
                return
            if self.drop_down_JobCardRefDetails.selected_value == job_id:
                return
            self._prewarm_for_bundle(job_id, modals, prewarmed, keys[idx])
            try:
                anvil.js.window.setTimeout(lambda: _bg_step(idx + 1), 0)
            except Exception:
                pass
        try:
            anvil.js.window.setTimeout(lambda: _bg_step(0), 0)
        except Exception:
            pass

    def _speculative_warm_batch(self, job_ids):
        lru = getattr(self, "_job_bundles_lru", None) or {}
        inflight = getattr(self, "_inflight_bundle_jobs", None)
        if inflight is None:
            self._inflight_bundle_jobs = inflight = set()
        missing = [jid for jid in (job_ids or ()) if jid and jid not in lru and jid not in inflight]
        if not missing:
            return
        inflight.update(missing)
        try:
            with anvil.server.no_loading_indicator:
                batch = anvil.server.call_s("get_progress_tracker_modals_batch", missing[:3]) or {}
            for raw_id, modals in batch.items():
                jid = int(raw_id) if str(raw_id).isdigit() else raw_id
                if modals:
                    self._store_modals_into_lru_and_active(jid, modals)
        except Exception:
            pass
        finally:
            for jid in missing:
                inflight.discard(jid)

    def _background_speculative_warm(self, job_id):
        self._speculative_warm_batch([job_id])

    def btn_SearchCustomer_click(self, **event_args):
        """Search JobCardRef or client Fullname in <2ms from ModCache, with 1-RPC cold fallback."""
        self.txtJobCardRef.text = (self.txtJobCardRef.text or "").strip()
        if not self.txtJobCardRef.text:
            alert(
                "Please enter job card ref to proceed.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.txtJobCardRef.focus()
            return

        search_value = self.txtJobCardRef.text
        smap = getattr(self, "_tracker_summary_map", None)
        if smap is None:
            self._tracker_summary_map = smap = {}

        idx_rows = getattr(ModGetData, "peekTrackerSearchIndexCached", lambda: None)()
        if idx_rows is not None:
            low = search_value.lower()
            matches = [
                r for r in idx_rows
                if low in r.get("ref_low", "") or low in r.get("name_low", "")
            ]
            for m in matches:
                jid = int(m["id"]) if str(m["id"]).isdigit() else m["id"]
                smap[jid] = m["summary"]
            result = [(m["label"], int(m["id"]) if str(m["id"]).isdigit() else m["id"]) for m in matches]
            self.drop_down_JobCardRefDetails.items = result
            if result:
                top_ids = [r[1] for r in result[:3]]
                try:
                    anvil.js.window.setTimeout(lambda: self._speculative_warm_batch(top_ids), 0)
                except Exception:
                    pass
            return

        with anvil.server.no_loading_indicator:
            payload = anvil.server.call("search_tracker_jobcards", search_value)

        if isinstance(payload, dict):
            raw_items = payload.get("items") or []
            result = [(lbl, int(jid) if str(jid).isdigit() else jid) for lbl, jid in raw_items]
            for raw_id, summary in (payload.get("summaries") or {}).items():
                jid = int(raw_id) if str(raw_id).isdigit() else raw_id
                smap[jid] = summary
            for raw_id, modals in (payload.get("top_modals") or {}).items():
                jid = int(raw_id) if str(raw_id).isdigit() else raw_id
                if modals:
                    self._store_modals_into_lru_and_active(jid, modals, summary=smap.get(jid))
        else:
            result = payload or []

        self.drop_down_JobCardRefDetails.items = result
        try:
            anvil.js.window.setTimeout(self._warm_search_index_async, 0)
            if result and len(result) > 1:
                next_ids = [r[1] for r in result[1:3]]
                anvil.js.window.setTimeout(lambda: self._speculative_warm_batch(next_ids), 0)
        except Exception:
            pass

    def drop_down_JobCardRefDetails_change(self, **event_args):
        """Render selected Job Card summary in <2ms from RAM cache and warm modals asynchronously."""
        if self.drop_down_JobCardRefDetails.selected_value:
            self.refresh_selected_job_card()
        else:
            alert(
                "Please enter job card ref to procced.",
                title="Blank Field(s) Found",
                large=False,
            )
            self.drop_down_JobCardRefDetails.focus()

    def _apply_tracker_ui(self, result):
        job_card = result["job_card"]
        client = result["client"]

        self.label_MakeAndModel.text = job_card["MakeAndModel"]
        self.label_Mileage.text = job_card["Mileage"]
        self.label_RegNo.text = job_card["RegNo"]
        self.label_date_received.text = job_card["ReceivedDate"]

        self.label_Owner.text = client["Fullname"]
        self.label_Phone.text = client["Phone"]

        self.populatePaymentDetails(result)

        effective_status = (
            result["invoice_status"]
            if job_card["Status"] == "Ready for Pickup"
            else job_card["Status"]
        )
        self.set_progress_state(
            effective_status,
            cancelled_reason=result.get("cancelled_reason", ""),
        )
        return effective_status

    def refresh_selected_job_card(self, force_server=False):
        job_id = self.drop_down_JobCardRefDetails.selected_value
        if not job_id:
            self._invalidate_modals_cache()
            return

        lru = getattr(self, "_job_bundles_lru", None)
        if not force_server and lru and job_id in lru:
            entry = lru[job_id]
            effective_status = self._apply_tracker_ui(entry["tracker"])
            self._modals_cache = entry["modals"]
            self._modals_cache_job_id = job_id
            self._prewarmed_modals = entry["prewarmed"]
            self._schedule_prewarm_modals(job_id, active_status=effective_status)
            return

        smap = getattr(self, "_tracker_summary_map", None)
        if not force_server and smap and job_id in smap:
            if self._modals_cache_job_id is not None and self._modals_cache_job_id != job_id:
                self._modals_cache = {}
                self._modals_cache_job_id = None
                self._prewarmed_modals = {}
            self._apply_tracker_ui(smap[job_id])
            try:
                anvil.js.window.setTimeout(lambda: self._speculative_warm_batch([job_id]), 0)
            except Exception:
                self._speculative_warm_batch([job_id])
            return

        if self._modals_cache_job_id is not None and self._modals_cache_job_id != job_id:
            self._modals_cache = {}
            self._modals_cache_job_id = None
            self._prewarmed_modals = {}

        with anvil.server.no_loading_indicator:
            result = anvil.server.call(
                "get_progress_tracker_data",
                job_id,
                True,
            )

            if not result:
                return

            effective_status = self._apply_tracker_ui(result)

        if smap is not None:
            smap[job_id] = {k: v for k, v in result.items() if k != "modals"}

        modals = result.get("modals")
        if modals is not None:
            new_prewarmed = {}
            self._modals_cache = modals
            self._modals_cache_job_id = job_id
            self._prewarmed_modals = new_prewarmed
            self._store_lru_job(job_id, result, modals, new_prewarmed)
            self._schedule_prewarm_modals(job_id, active_status=effective_status)
        else:
            self._schedule_prefetch_modals(job_id)

    def set_progress_state(self, active_state, cancelled_reason=""):
        """Highlight the active workflow step and show cancellation reason if needed."""
        status_labels = {
            "Checked In": self.label_checked_in,
            "Create Quote": self.label_create_quote,
            "Confirm Quote": self.label_confirm_quote,
            "In Service": self.label_in_service,
            "Verify Task": self.label_verify_task,
            "Issue Invoice": self.label_issue_invoice,
            "Cancel Jobcard": self.label_cancelled,
            "Pending": self.label_payment_due,
            "Paid": self.label_payment_done,
            "Complete": self.label_completed,
        }

        for status, label in status_labels.items():
            if status == active_state:
                label.background = "black"
                label.foreground = "white"
            else:
                label.background = "white"
                label.foreground = "black"

        if active_state == "Cancel Jobcard":
            # Use pre-fetched reason — no extra server call needed
            self.text_area_1.text = cancelled_reason
            self.text_area_1.visible = True
        else:
            self.text_area_1.visible = False
            
    def populatePaymentDetails(self, result):
        """Populate payment labels from pre-fetched tracker data (no server call)."""
        invoice_status   = result.get("invoice_status")
        self.label_Due.text  = result.get("invoice_total", 0)
        self.label_Paid.text = result.get("previous_payment", 0)

        if invoice_status == "Pending":
            if self.label_Paid.text == 0:
                self.label_Balance.text = self.label_Due.text
            else:
                bal = float(str(self.label_Due.text).replace(",", "")) - float(str(self.label_Paid.text).replace(",", ""))
                self.label_Balance.text = f"{bal:,.2f}"
            self.label_Discount.text = 0  # Discount may be issued upon final balance payment

        elif invoice_status == "Paid":
            bal = float(str(self.label_Due.text).replace(",", "")) - float(str(self.label_Paid.text).replace(",", ""))
            if bal > 0:  # Discount has been issued
                self.label_Discount.text = f"{bal:,.2f}"
                self.label_Balance.text = 0
        elif self.label_Due.text == 0 and self.label_Paid.text == 0:  # No invoice issued
            self.label_Discount.text = 0
            self.label_Balance.text = 0

    def btn_JobCard_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_JobCard.enabled = False
        try:
            job_id = self.drop_down_JobCardRefDetails.selected_value
            if not job_id:
                alert("No data found for the selected Job ID.", title="Missing Job Card Data", large=False)
                return

            jobcard_data = self._get_cached_or_fetch(job_id, "jobcard", "get_jobcard_form_data")
            if not jobcard_data:
                alert("No data found for the selected Job ID.", title="Missing Job Card Data", large=False)
                return

            form_inst = self._pop_or_build_modal(job_id, "jobcard", jobcard_data)
            outcome = alert(
                content=form_inst,
                buttons=[],
                dismissible=False,
                large=True,
            )
            if outcome == "updated":
                if self._modals_cache_job_id != job_id or not self._modals_cache:
                    self.refresh_selected_job_card(force_server=True)
            else:
                self._schedule_prewarm_single_modal(job_id, "jobcard")
        finally:
            self.btn_JobCard.enabled = True

    def btn_Defects_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Defects.enabled = False
        try:
            job_id = self.drop_down_JobCardRefDetails.selected_value
            if not job_id:
                alert("No data found for the selected Job ID.", title="Missing Defects Data", large=False)
                return

            defects_init_data = self._get_cached_or_fetch(job_id, "defects", "get_defects_form_init_data")
            if not defects_init_data:
                alert("No data found for the selected Job ID.", title="Missing Defects Data", large=False)
                return

            form_inst = self._pop_or_build_modal(job_id, "defects", defects_init_data)
            outcome = alert(
                content=form_inst,
                buttons=[],
                dismissible=False,
                large=True,
            )
            if outcome == "updated":
                self.refresh_selected_job_card(force_server=True)
            else:
                self._schedule_prewarm_single_modal(job_id, "defects")
        finally:
            self.btn_Defects.enabled = True

    def btn_Quotation_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Quotation.enabled = False
        try:
            job_id = self.drop_down_JobCardRefDetails.selected_value
            if not job_id:
                alert("No data found for the selected Job ID.", title="Missing Quotation Data", large=False)
                return

            quote_data = self._get_cached_or_fetch(job_id, "quote", "get_quote_details_by_job_id")
            if not quote_data:
                alert("No data found for the selected Job ID.", title="Missing Quotation Data", large=False)
                return

            form_inst = self._pop_or_build_modal(job_id, "quote", quote_data)
            alert(
                content=form_inst,
                buttons=[],
                dismissible=False,
                large=True,
            )
            self._schedule_prewarm_single_modal(job_id, "quote")
        finally:
            self.btn_Quotation.enabled = True

    def btn_Confirmed_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Confirmed.enabled = False
        try:
            job_id = self.drop_down_JobCardRefDetails.selected_value
            if not job_id:
                Notification("No data found for the selected Job ID.", title='Missing Quotation Data', style="danger", timeout=3).show()
                return

            quote_data = self._get_cached_or_fetch(job_id, "confirm", "get_quote_confirmation_details_by_job_id")
            if not quote_data:
                Notification("No data found for the selected Job ID.", title='Missing Quotation Data', style="danger", timeout=3).show()
                return

            form_inst = self._pop_or_build_modal(job_id, "confirm", quote_data)
            alert(content=form_inst, buttons=[], dismissible=False, large=True)
            self._schedule_prewarm_single_modal(job_id, "confirm")
        finally:
            self.btn_Confirmed.enabled = True

    def btn_Invoice_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Invoice.enabled = False
        try:
            job_id = self.drop_down_JobCardRefDetails.selected_value
            if not job_id:
                alert("No data found for the selected Job ID.", title="Missing Invoice Data", large=False)
                return

            quote_data = self._get_cached_or_fetch(job_id, "invoice", "get_invoice_details_by_job_id")
            if not quote_data:
                alert("No data found for the selected Job ID.", title="Missing Invoice Data", large=False)
                return

            form_inst = self._pop_or_build_modal(job_id, "invoice", quote_data)
            alert(
                content=form_inst,
                buttons=[],
                dismissible=False,
                large=True,
            )
            self._schedule_prewarm_single_modal(job_id, "invoice")
        finally:
            self.btn_Invoice.enabled = True

    def btn_Payment_click(self, **event_args):
        """This method is called when the button is clicked"""
        self.btn_Payment.enabled = False
        try:
            job_id = self.drop_down_JobCardRefDetails.selected_value
            if not job_id:
                alert("No data found for the selected Job ID.", title="Missing Payment Data", large=False)
                return

            payment_data = self._get_cached_or_fetch(job_id, "payment", "getPaymentsDetails")
            if not payment_data:
                alert("No data found for the selected Job ID.", title="Missing Payment Data", large=False)
                return

            form_inst = self._pop_or_build_modal(job_id, "payment", payment_data)
            outcome = alert(
                content=form_inst,
                buttons=[],
                dismissible=False,
                large=True,
            )
            if outcome == "updated":
                self.refresh_selected_job_card(force_server=True)
            else:
                self._schedule_prewarm_single_modal(job_id, "payment")
        finally:
            self.btn_Payment.enabled = True


    def btn_ViewInspection_click(self, **event_args):
        self.btn_ViewInspection.enabled=False
        job_id = self.drop_down_JobCardRefDetails.selected_value
        if not job_id:
            notification_timeout = 3
            Notification(
                "Please select Jobcard ref to proceed.",
                title='Missing Jobcard Ref',
                style="danger",
                timeout=notification_timeout,
            ).show()
            anvil.js.window.setTimeout(
                lambda: setattr(self.btn_ViewInspection, "enabled", True),
                notification_timeout * 1000,
            )
            return

        alert(content=VehicleInspectionChecklist(job_id), buttons=[], dismissible=False, large=True)
        self.btn_ViewInspection.enabled=True
