import os

import supervisely as sly

from dotenv import load_dotenv

if sly.is_development():
    load_dotenv("local.env")
    load_dotenv(os.path.expanduser("~/supervisely.env"))

api: sly.Api = sly.Api.from_env()

SLY_APP_DATA_DIR = sly.app.get_data_dir()
ABSOLUTE_PATH = os.path.dirname(__file__)

# Defining the path to the directory where the images will be saved and creating it if it doesn't exist.
STATIC_DIR = os.path.join(SLY_APP_DATA_DIR, "static")
os.makedirs(STATIC_DIR, exist_ok=True)


class State:
    def __init__(self):
        self.selected_team = sly.io.env.team_id()
        self.selected_workspace = sly.io.env.workspace_id()
        self.selected_project = sly.io.env.project_id(raise_not_found=False)
        self.selected_dataset = sly.io.env.dataset_id(raise_not_found=False)

        self.batch_size = None
        self.new_tag_name = None
        self.automatic_tagging = None

        self.image_infos = []

        self.project_meta = None

        self.pages = {}

        self.current_page_number = None

        self.tagged_images = []

        self.continue_tagging = True

    def save_project_meta(self):
        sly.logger.debug(
            f"Trying to receive project meta from the API for project ID {self.selected_project}."
        )

        project_meta_json = api.project.get_meta(self.selected_project)
        self.project_meta = sly.ProjectMeta.from_json(project_meta_json)

        sly.logger.debug("Readed project meta and saved it in the global state.")


STATE = State()
