from gimpfu import *


def copy_layer(image, layer):
    copied = layer.copy(1)
    image.insert_layer(copied)
    return copied


def extract_rgb(image, layer, color):
    orig_name = layer.name
    temp = copy_layer(image, layer)

    # discard alpha by setting the output range to (1,1)
    pdb.gimp_drawable_levels(temp, 4, 0, 1, False, 0.1, 1, 1, False)
    rr = int(color == 'R')
    gg = int(color == 'G')
    bb = int(color == 'B')
    pdb.plug_in_colors_channel_mixer(image, temp, 0, rr, 0, 0, 0, gg, 0, 0, 0, bb)
    # make white
    pdb.plug_in_colors_channel_mixer(image, temp, 0, rr, gg, bb, rr, gg, bb, rr, gg, bb)
    temp.name = orig_name + '_' + color


def extract_alpha(image, layer):
    orig_name = layer.name
    temp = copy_layer(image, layer)

    temp.add_mask(temp.create_mask(3)) # Create mask from layer's alpha
    temp.fill(2) # fill with white
    temp2 = pdb.gimp_layer_new(image, temp.width, temp.height, 1, temp.name + '_', 100, 28) # 100 opacity, 28 = normal blend mode
    image.insert_layer(temp2, position=1) # below temp layer
    old_bg = pdb.gimp_context_get_background()
    pdb.gimp_context_set_background((0, 0, 0, 0))
    temp2.fill(1)
    pdb.gimp_context_set_background(old_bg)
    temp.remove_mask(0) # apply mask
    merged = image.merge_down(temp, 0)
    merged.name = orig_name + '_A'


def _real_extract(image, drawable):
    source_layer = image.layers[0]
    for t in ['A', 'B', 'G', 'R']:
        if t == 'A':
            extract_alpha(image, source_layer)
        else:
            extract_rgb(image, source_layer, t)


def extract_x2(image, drawable):
    _real_extract(image, drawable)

register(
    'python-fu-extract_x2',
    'Extract components as colored layers',
    'Extract components as colored layers',
    'Zak',
    'WTFPL',
    '',
    '<Image>/File/Extract x2 components as layers...',
    '*',
    [],
    [],
    extract_x2)

main()