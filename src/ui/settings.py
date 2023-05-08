import supervisely as sly

from supervisely.app.widgets import (
    Container,
    Card,
    Input,
    InputNumber,
    Button,
    Field,
    Checkbox,
    Text,
)

import src.globals as g
import src.ui.tagging as tagging

batch_size_input = InputNumber(value=30, min=1, max=100)
batch_size_field = Field(
    title="Batch size",
    description="Number of images to process in one iteration.",
    content=batch_size_input,
)

new_tag_name_input = Input(placeholder="Enter tag name", minlength=1)
new_tag_name_field = Field(
    title="New tag name",
    description="Enter name of new the tag, that will be added to images.",
    content=new_tag_name_input,
)

automatic_tagging_checkbox = Checkbox("Start next batch automatically")
automatic_tagging_field = Field(
    title="Automatic tagging",
    description="If checked, the next batch will be tagged automatically.",
    content=automatic_tagging_checkbox,
)

save_settings_button = Button("Save settings", icon="zmdi zmdi-floppy")
change_settins_button = Button("Change settings", icon="zmdi zmdi-settings")
change_settins_button.hide()

no_tag_name_text = Text("Enter tag name before saving settings.", status="warning")
no_tag_name_text.hide()


card = Card(
    title="2️⃣ Settings",
    description="Configure settings for the tagging.",
    content=Container(
        [
            batch_size_field,
            new_tag_name_field,
            automatic_tagging_field,
            save_settings_button,
            change_settins_button,
            no_tag_name_text,
        ]
    ),
    lock_message="Select the dataset on step 1️⃣.",
    collapsable=True,
)
card.lock()
card.collapse()


@save_settings_button.click
def save_settings():
    no_tag_name_text.hide()

    g.STATE.batch_size = batch_size_input.get_value()
    g.STATE.new_tag_name = new_tag_name_input.get_value()
    g.STATE.automatic_tagging = automatic_tagging_checkbox.is_checked()

    if not g.STATE.new_tag_name:
        sly.logger.warning(
            "Save settings button was clicked, but new tag name is empty."
        )
        no_tag_name_text.show()
        return

    sly.logger.debug(
        f"Preview button was clicked. Saved batch size: {g.STATE.batch_size} "
        f"and new tag name: {g.STATE.new_tag_name} in global state. "
        f"Automatic tagging is {g.STATE.automatic_tagging}."
    )
    card.collapse()

    batch_size_input.disable()
    new_tag_name_input.disable()
    automatic_tagging_checkbox.disable()
    save_settings_button.hide()

    pagination()

    g.STATE.save_project_meta()

    tagging.update_current_batch_gallery()

    change_settins_button.show()

    tagging.card.unlock()
    tagging.card.uncollapse()


@change_settins_button.click
def change_settings():
    sly.logger.debug("Change settings button was clicked.")
    card.uncollapse()

    batch_size_input.enable()
    new_tag_name_input.enable()
    automatic_tagging_checkbox.enable()
    save_settings_button.show()
    change_settins_button.hide()

    tagging.card.lock()
    tagging.card.collapse()


def pagination():
    g.STATE.image_infos = sorted(
        g.api.image.get_list(g.STATE.selected_dataset), key=lambda x: x.name
    )

    sly.logger.debug(
        f"Retreived {len(g.STATE.image_infos)} images from dataset and saved them in global state."
    )

    g.STATE.pages.clear()

    sly.logger.debug(f"Cleared pages in global state. Pages: {g.STATE.pages}.")

    pages_number = len(g.STATE.image_infos) // g.STATE.batch_size
    if len(g.STATE.image_infos) % g.STATE.batch_size != 0:
        pages_number += 1

    sly.logger.debug(f"Calculated number of pages: {pages_number}.")

    for page_number in range(1, pages_number + 1):
        g.STATE.pages[page_number] = g.STATE.image_infos[
            g.STATE.batch_size * (page_number - 1) : g.STATE.batch_size * page_number
        ]

    sly.logger.debug(
        "Created pages dict and saved it in global state. "
        f"Number of items on last page: {len(g.STATE.pages[pages_number])}."
    )

    g.STATE.current_page_number = 1

    sly.logger.debug(
        f"Saved current page number: {g.STATE.current_page_number} in global state."
    )

    g.STATE.tagged_images.clear()

    sly.logger.debug(f"Cleared tagged images in global state.")
