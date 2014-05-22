
def resize_image(dest_fn, src_fn, x, y, fmt="JPEG", keep_aspect=False,
        crop=False):
    """
    Resize image and write it out.
    """
    from PIL import Image
    im = Image.open(src_fn)
    if keep_aspect:
        im.thumbnail((x, y), Image.ANTIALIAS)
    else:
        if crop:
            raise NotImplementedError("Crop-based resizing not implemented")
        else:
            im = im.resize((x, y), Image.ANTIALIAS)
    im.save(dest_fn, fmt)
    return im


def do_image_resizing(image, camera, subsec=0, keep_aspect=False,
        crop=False):
    resolutions = camera[FIELDS["resolutions"]]

    if len(resolutions) == 1 and resolutions[0] in FULLRES_CONSTANTS:
        # there's no down-sizing to do, so get out now.
        return

    in_ext = path.splitext(image)[-1].lstrip(".")
    image_date = get_file_date(image, camera[FIELDS["interval"]] * 60)
    if not image_date:
        return
    for resolution in resolutions:
        if isinstance(resolution, str):
            # fullres
            continue
        x, y = resolution
        resized_name = make_timestream_name(camera, res=resolution)
        resized_image = get_new_file_name(image_date, resized_name,
                    n=subsec, ext=in_ext)
        resized_image = path.join(
            camera[FIELDS["destination"]],
            resized_name,
            resized_image
            )

        out_dir = path.dirname(resized_image)
        if not path.exists(out_dir):
            # makedirs is like `mkdir -p`, creates parents, but raises
            # os.error if target already exits
            os.makedirs(out_dir)
            #TODO: implement try/except. for now, just let the error crash it

        resize_image(resized_image, image, x, y, keep_aspect=keep_aspect,
                crop=crop)


