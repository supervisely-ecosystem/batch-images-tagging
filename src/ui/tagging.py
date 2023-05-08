from random import choice

import supervisely as sly

from supervisely.app.widgets import (
    Container,
    Card,
    Button,
    RadioTabs,
    GridGallery,
    Flexbox,
    Progress,
    Text,
    Checkbox,
    Transfer,
    Sidebar,
)

import src.globals as g

page_text = Text(status="info")
page_text.hide()

success_text = Text(status="success")
error_text = Text(status="error")
success_text.hide()
error_text.hide()

text_container = Container([success_text, error_text])

prev_batch_button = Button("Previous batch", icon="zmdi zmdi-arrow-left")
next_batch_button = Button("Next batch", icon="zmdi zmdi-arrow-right")
random_batch_button = Button("Random batch", icon="zmdi zmdi-shuffle")
start_batch_button = Button(
    "Add tags to batch", icon="zmdi zmdi-play", button_type="success"
)
stop_batch_button = Button("Stop tagging", icon="zmdi zmdi-stop", button_type="danger")
stop_batch_button.hide()

buttons_flexbox = Flexbox(
    [
        prev_batch_button,
        random_batch_button,
        start_batch_button,
        stop_batch_button,
        next_batch_button,
    ],
    center_content=True,
)

batch_tagging_progress = Progress()
batch_tagging_progress.hide()

global_tagging_progress = Progress(hide_on_finish=False)
global_tagging_progress.hide()

current_batch_gallery = GridGallery(columns_number=5)
apply_to_all_checkbox = Checkbox("Apply tag to all images", checked=True)

select_images_transfer = Transfer(
    filterable=True,
    filter_placeholder="Search images by name",
    titles=["Images to skip", "Images to tag"],
)
select_images_transfer.disable()
current_batch_sidebar = Sidebar(
    left_content=Container([select_images_transfer]),
    right_content=Container([page_text, apply_to_all_checkbox, current_batch_gallery]),
    width_percent="40%",
)

processed_images_gallery = GridGallery(columns_number=5)

gallery_tabs = RadioTabs(
    ["Current batch", "Processed images"],
    contents=[current_batch_sidebar, processed_images_gallery],
    descriptions=[
        "Images from the batch that will be tagged.",
        "Images that were tagged.",
    ],
)

card = Card(
    title="3️⃣ Tagging",
    description="Select the batch, tag images and preview the results.",
    content=Container(
        [
            buttons_flexbox,
            batch_tagging_progress,
            global_tagging_progress,
            text_container,
            gallery_tabs,
        ]
    ),
    lock_message="Save settings on step 2️⃣.",
    collapsable=True,
)
card.lock()
card.collapse()


def update_current_batch_gallery():
    start_batch_button.enable()

    page_text.hide()
    current_batch_gallery.loading = True

    apply_to_all_checkbox.check()

    page_text.text = f"Showing images from batch {g.STATE.current_page_number} of {len(g.STATE.pages)}."
    page_text.show()

    sly.logger.debug("Trying to update current batch gallery.")

    current_batch_images = g.STATE.pages[g.STATE.current_page_number]

    current_batch_gallery.clean_up()
    handle_buttons()

    sly.logger.debug("Cleaned up current batch gallery.")

    if len(current_batch_images) == 0:
        sly.logger.warning(
            f"Current batch on page {g.STATE.current_page_number} is empty."
        )
        current_batch_gallery.loading = False

        page_text.text += " All images from this batch were tagged."

        start_batch_button.disable()

        select_images_transfer.set_items([])

        return

    sly.logger.debug(
        f"Readed {len(current_batch_images)} images for current batch from "
        f"page with number {g.STATE.current_page_number}."
    )

    image_ids = [image_info.id for image_info in current_batch_images]

    sly.logger.debug(f"Created list of image ids: {image_ids} for current batch.")

    anns_json = g.api.annotation.download_json_batch(
        g.STATE.selected_dataset, image_ids
    )

    sly.logger.debug(
        f"Downloaded {len(anns_json)} annotations in JSON format for current batch."
    )

    anns = []

    sly.logger.debug("Trying to create annotation objects from JSON.")

    for ann_json in anns_json:
        ann = sly.Annotation.from_json(ann_json, g.STATE.project_meta)
        anns.append(ann)

    sly.logger.debug(f"Created {len(anns)} annotation objects from JSON.")

    image_urls = [image.preview_url for image in current_batch_images]

    sly.logger.debug(f"Created {len(image_urls)} image urls for current batch.")

    image_names = [image.name for image in current_batch_images]

    select_images_transfer.set_items(image_names)
    select_images_transfer.set_transferred_items(image_names)
    select_images_transfer.show()

    sly.logger.debug(
        f"Created {len(image_names)} image names for current batch. "
        "Trying to add URLS, annotations and names to current batch gallery."
    )

    for image_url, ann, image_name in zip(image_urls, anns, image_names):
        current_batch_gallery.append(image_url, ann, image_name)

    current_batch_gallery.loading = False

    sly.logger.debug("Added URLS and annotations to current batch gallery.")


@prev_batch_button.click
def previous_batch():
    sly.logger.debug("Previous batch button was clicked.")
    g.STATE.current_page_number -= 1
    update_current_batch_gallery()
    hide_texts()


@next_batch_button.click
def next_batch():
    sly.logger.debug("Next batch button was clicked.")
    g.STATE.current_page_number += 1
    update_current_batch_gallery()
    hide_texts()


@random_batch_button.click
def random_batch():
    sly.logger.debug("Random batch button was clicked.")
    g.STATE.current_page_number = choice(list(g.STATE.pages.keys()))
    update_current_batch_gallery()
    hide_texts()


def handle_buttons():
    if len(g.STATE.pages) == 1:
        sly.logger.debug(
            "There's only one page in pages dictionary, all buttons will be disabled."
        )

        prev_batch_button.disable()
        next_batch_button.disable()
        random_batch_button.disable()

    elif g.STATE.current_page_number == 1:
        sly.logger.debug("First page is selected, disabling previous batch button.")

        prev_batch_button.disable()
        next_batch_button.enable()

    elif g.STATE.current_page_number == max(g.STATE.pages.keys()):
        sly.logger.debug("Last page is selected, disabling next batch button.")

        prev_batch_button.enable()
        next_batch_button.disable()
    else:
        sly.logger.debug("Middle page is selected, enabling all buttons.")

        prev_batch_button.enable()
        next_batch_button.enable()


@apply_to_all_checkbox.value_changed
def apply_to_all_checkbox_changed(is_checked):
    if not is_checked:
        select_images_transfer.set_transferred_items([])
        start_batch_button.disable()
    else:
        select_images_transfer.set_transferred_items(
            select_images_transfer.get_items_keys()
        )
        start_batch_button.enable()


@select_images_transfer.value_changed
def select_images_transfer_changed(keys):
    if len(select_images_transfer.get_transferred_items()) == len(
        select_images_transfer.get_items_keys()
    ):
        apply_to_all_checkbox.check()
    else:
        apply_to_all_checkbox.uncheck()

    if len(select_images_transfer.get_transferred_items()) == 0:
        start_batch_button.disable()
    else:
        start_batch_button.enable()


@start_batch_button.click
def tag_batch():
    start_batch_button.hide()
    stop_batch_button.show()

    g.STATE.continue_tagging = True

    sly.logger.debug("Start batch button was clicked, trying to tag batch.")

    if apply_to_all_checkbox.is_checked():
        sly.logger.debug("Apply to all checkbox is checked, will tag all images.")

        image_ids = [image.id for image in g.STATE.pages[g.STATE.current_page_number]]

    else:
        sly.logger.debug(
            "Apply to all checkbox is not checked, will tag transferred images from transfer widget."
        )

        image_names = select_images_transfer.get_transferred_items()

        image_ids = [
            image.id
            for image in g.STATE.pages[g.STATE.current_page_number]
            if image.name in image_names
        ]

    sly.logger.info(
        f"Created list of image ids for current batch with {len(image_ids)} images."
    )

    tag_meta = get_tag_meta(g.STATE.new_tag_name)

    global_tagging_progress.show()
    batch_tagging_progress.show()

    image_ids_with_tags = []
    image_ids_with_errors = []

    with global_tagging_progress(
        message="Progress of tagging images in dataset...",
        total=len(g.STATE.image_infos),
        initial=len(g.STATE.tagged_images),
    ) as global_pbar:
        with batch_tagging_progress(
            message="Progress of tagging images in current batch...",
            total=len(image_ids),
        ) as batch_pbar:
            for image_id in image_ids:
                if not g.STATE.continue_tagging:
                    sly.logger.info("Stop button was clicked, stopping tagging.")
                    break

                try:
                    g.api.image.add_tag(image_id, tag_meta.sly_id)
                    image_ids_with_tags.append(image_id)

                    batch_pbar.update(1)
                    global_pbar.update(1)

                except Exception as e:
                    sly.logger.error(
                        f"There was an error while tagging image with id {image_id}: {e}."
                    )
                    image_ids_with_errors.append(image_id)

    batch_tagging_progress.hide()

    stop_batch_button.hide()
    start_batch_button.show()

    sly.logger.info(
        f"Tagging of batch on page {g.STATE.current_page_number} finished. "
        f"Succesfully tagged {len(image_ids_with_tags)} images. Number of errors: {len(image_ids_with_errors)}. "
        f"Image ids with errors: {image_ids_with_errors}."
    )

    if len(image_ids_with_errors) > 0:
        error_text.text = (
            f"Number of errors: {len(image_ids_with_errors)}. "
            f"Image ids with errors: {', '.join(image_ids_with_errors)}."
        )
        error_text.show()

    update_galleries(image_ids_with_tags)

    if g.STATE.automatic_tagging and g.STATE.current_page_number < max(
        g.STATE.pages.keys()
    ):
        sly.logger.debug("Automatic tagging is enabled, will tag next batch.")
        next_batch()
        tag_batch()

    success_text.text = (
        f"Successfully tagged {len(image_ids_with_tags)} images. "
        f"Overall progress of tagging images in dataset: {len(g.STATE.tagged_images)}/{len(g.STATE.image_infos)}."
    )
    success_text.show()


def update_galleries(image_ids_with_tags):
    current_image_infos = g.STATE.pages[g.STATE.current_page_number]
    updated_image_infos = [
        image_info
        for image_info in current_image_infos
        if image_info.id not in image_ids_with_tags
    ]

    sly.logger.debug(
        f"Created list of not processed images from current batch with {len(updated_image_infos)} images."
    )

    tagged_image_infos = [
        image_info
        for image_info in current_image_infos
        if image_info.id in image_ids_with_tags
    ]

    sly.logger.debug(
        f"Created list of tagged images from current batch with {len(tagged_image_infos)} images."
    )

    g.STATE.pages[g.STATE.current_page_number] = updated_image_infos
    g.STATE.tagged_images.extend(tagged_image_infos)

    sly.logger.debug(
        "Updated current page data in global state. Added list of tagged images to global state. "
        f"Now g.STATE.tagged_images has {len(g.STATE.tagged_images)} images."
    )

    update_current_batch_gallery()

    anns_json = g.api.annotation.download_json_batch(
        g.STATE.selected_dataset, image_ids_with_tags
    )

    sly.logger.debug(
        f"Downloaded {len(anns_json)} annotations in JSON format for tagged images."
    )

    anns = []

    sly.logger.debug("Trying to create annotation objects from JSON.")

    for ann_json in anns_json:
        ann = sly.Annotation.from_json(ann_json, g.STATE.project_meta)
        anns.append(ann)

    sly.logger.debug(
        "Starting to updating processed images gallery with tagged images."
    )

    processed_images_gallery.loading = True
    for tagged_image_info, ann in zip(tagged_image_infos, anns):
        processed_images_gallery.append(
            tagged_image_info.preview_url, ann, tagged_image_info.name
        )

    processed_images_gallery.loading = False

    sly.logger.debug("Updated processed image gallery.")


def hide_texts():
    success_text.hide()
    error_text.hide()


@stop_batch_button.click
def stop_batch():
    sly.logger.debug("Stop batch button was clicked.")

    g.STATE.continue_tagging = False
    stop_batch_button.hide()
    start_batch_button.show()


def get_tag_meta(tag_name) -> sly.TagMeta:
    sly.logger.debug(f"Getting tag meta for tag name: {tag_name}")

    if g.STATE.project_meta.tag_metas.get(tag_name) is not None:
        sly.logger.info(f"Tag meta for tag name {tag_name} already exists.")

        return g.STATE.project_meta.tag_metas.get(tag_name)

    sly.logger.info(f"Tag meta for tag name {tag_name} does not exist. Creating it.")

    tag_meta = sly.TagMeta(tag_name, sly.TagValueType.NONE)
    tagged_project_meta = g.STATE.project_meta.add_tag_meta(tag_meta)

    sly.logger.debug(
        f"Created tag meta for tag with name {tag_name} locally. Trying to update project meta on server."
    )

    g.api.project.update_meta(g.STATE.selected_project, tagged_project_meta)

    sly.logger.info("Updated project meta on server.")

    meta_json = g.api.project.get_meta(g.STATE.selected_project)
    g.STATE.project_meta = sly.ProjectMeta.from_json(meta_json)

    sly.logger.debug("Updated project in global state after adding new tag meta.")

    return g.STATE.project_meta.tag_metas.get(tag_name)
