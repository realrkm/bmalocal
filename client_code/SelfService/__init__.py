from ._anvil_designer import SelfServiceTemplate
from anvil import *
import anvil.server
import anvil.users
import anvil.tables as tables
import anvil.tables.query as q
from anvil.tables import app_tables
import anvil.js
import base64


_INSPECTION_IMAGE_CODES = ("image_1", "image_2", "image_3")
_INSPECTION_IMAGE_TYPES = {"image/jpeg", "image/png", "image/webp"}
_MAX_INSPECTION_IMAGE_BYTES = 10 * 1024 * 1024
_BASE64_ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/"


class SelfService(SelfServiceTemplate):
    def __init__(self, **properties):
        # Set Form properties and Data Bindings.
        self.init_components(**properties)

        # Any code you write here will run before the form opens.
        anvil.js.call('replaceBanner')       
        
    def getCarPartNamesAndCategory(self):
        return anvil.server.call('getCarPartNamesAndCategory')

    def get_technician_jobcards_by_status(self):
        return anvil.server.call("get_technician_jobcards_by_status")

    def get_technicians_list(self):
        return anvil.server.call_s('get_technicians_list')
        
    def save_work_done(self, jobcardref, workdone):
        anvil.server.call("save_work_done_by_technician", jobcardref, workdone)
        return None

    def storeTechDetails(
        self,
        jobcard_ref,
        tech_notes,
        defects,
        parts,
        technician,
        signature_data,
        checklist=None,
        inspection_images=None,
    ):
        inspection_media = (
            self._inspection_photo_media(inspection_images)
            if checklist
            else None
        )
        signature = self.get_signature_image(signature_data)
        JobCardID = anvil.server.call_s("getJobCardID", jobcard_ref)
        if parts is None:
            parts = "None"
        anvil.server.call(
            "saveOrUpdateTechnicianPortalDefectsAndRequestedParts",
            JobCardID,
            tech_notes,
            defects,
            parts,
            technician,
            signature,
            checklist,
            inspection_media,
        )
        return None

    @staticmethod
    def _inspection_photo_media(images):
        if not isinstance(images, dict) or set(images) != set(_INSPECTION_IMAGE_CODES):
            raise ValueError("Please upload all three vehicle inspection photos.")

        media = {}
        for image_code, data_url in images.items():
            if not isinstance(data_url, str) or "," not in data_url:
                raise ValueError("Please upload all three vehicle inspection photos.")
            header, encoded = data_url.split(",", 1)
            content_type = header[5:].split(";", 1)[0].lower() if header.startswith("data:") else ""
            if content_type not in _INSPECTION_IMAGE_TYPES or ";base64" not in header:
                raise ValueError("Use JPEG, PNG, or WebP files for inspection photos.")
            padding = len(encoded) - len(encoded.rstrip("="))
            payload = encoded[:-padding] if padding else encoded
            expected_remainder = (0, 3, 2)
            if (
                len(encoded) % 4
                or padding > 2
                or len(payload) % 4 != expected_remainder[padding]
                or any(character not in _BASE64_ALPHABET for character in payload)
            ):
                raise ValueError("An inspection photo could not be read.")
            try:
                image_bytes = base64.b64decode(encoded)
            except (ValueError, TypeError):
                raise ValueError("An inspection photo could not be read.")
            if not image_bytes or len(image_bytes) > _MAX_INSPECTION_IMAGE_BYTES:
                raise ValueError("Inspection photos must be smaller than 10 MB.")
            media[image_code] = BlobMedia(
                content_type, image_bytes, name=image_code
            )
        return media

    def getVehicleInspectionPhotos(self, jobcard_ref):
        jobcard_id = anvil.server.call("getJobCardID", jobcard_ref)
        if not jobcard_id:
            return {image_code: None for image_code in _INSPECTION_IMAGE_CODES}

        inspection_data = anvil.server.call(
            "get_vehicle_inspection_data", jobcard_id
        )
        images = inspection_data.get("images", {}) if isinstance(inspection_data, dict) else {}
        return {
            image_code: (
                "data:{};base64,{}".format(
                    photo.content_type,
                    base64.b64encode(photo.get_bytes()).decode("ascii"),
                )
                if photo is not None
                else None
            )
            for image_code in _INSPECTION_IMAGE_CODES
            for photo in (images.get(image_code),)
        }

    def get_signature_image(self, signature_data):
        
        data_url = signature_data

        # Split data URL to get the base64 content
        header, encoded = data_url.split(",", 1)
        binary_data = base64.b64decode(encoded)

        # Create an Anvil Media object
        media = BlobMedia("image/png", binary_data, name="signature.png")

        # Return or store the media for further use
        return media

    def get_jobcard_and_defect_details(self, jobcardref):
        return anvil.server.call("get_jobcard_and_defect_details", jobcardref)

    def getCustomerFeedback(self, jobcardref):
        return anvil.server.call("get_parts_and_feedback_by_jobcardref", jobcardref)

    def logoutUser(self):
        try:
            import anvil.js
            anvil.js.call("disconnectWtChat")
        except Exception:
            pass
        open_form('LogoutBackground')
        anvil.users.logout()