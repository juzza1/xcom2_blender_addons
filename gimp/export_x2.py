import os
import os.path
import re

from gimpfu import *


def hide_all(layer_container):
    for layer in layer_container.layers:
        layer.visible = False
        if isinstance(layer, gimp.GroupLayer):
            hide_all(layer)


def _real_export(image, temp):
    hide_all(temp)
    for layer in temp.layers:
        if not layer.name.startswith('_'):
            continue
        layer.visible = True
        if isinstance(layer, gimp.GroupLayer):
            channel_merge = False
            for grouped_layer in layer.layers:
                grouped_layer.visible = True
                if grouped_layer.mask:
                    grouped_layer.apply_mask = True
                # channel composition
                # Cant have duplicate layer names even in different groups,
                # so assume anything matching the regex is for compositing
                m = re.match(r'(R?G?B?A?)\b', grouped_layer.name)
                if m:
                    composition_rule = m.group(1)
                    if isinstance(grouped_layer, gimp.GroupLayer):
                        for clayer in grouped_layer.layers:
                            clayer.visible = True
                        comp_layer = pdb.gimp_image_merge_layer_group(temp, grouped_layer)
                    else:
                        comp_layer = grouped_layer
                    rr = int('R' in composition_rule)
                    gg = int('G' in composition_rule)
                    bb = int('B' in composition_rule)
                    if rr or gg or bb:
                        pdb.plug_in_colors_channel_mixer(temp, comp_layer, 0, rr, 0, 0, 0, gg, 0, 0, 0, bb)
                        comp_layer.mode = 33 # Addition mode
                        channel_merge = True
                    else: # alpha
                        mask = pdb.gimp_layer_create_mask(comp_layer, 5) # 5 = grayscale copy of layer
                        pdb.gimp_layer_add_mask(layer, mask)
                        pdb.gimp_image_remove_layer(temp, comp_layer)
            # set last layer to 28 = normal mode if we are doing channel composition
            # don't actually know when we wouldn't want to do this,
            # but only do it when actually required, just in case
            if channel_merge:
                layer.layers[-1].mode = 28
            layer = pdb.gimp_image_merge_layer_group(temp, layer)
        if layer.mask:
            pdb.gimp_image_remove_layer_mask(temp, layer, 0)
        outdir = os.path.join(os.path.dirname(image.filename), 'tga_out')
        if not os.path.exists(outdir):
            os.mkdir(outdir)
        outfile = os.path.join(outdir, layer.name[1:] + '.tga')
        pdb.gimp_file_save(temp, layer, outfile, outfile)
        layer.visible = False


def export_x2(image, drawable):
    temp = pdb.gimp_image_duplicate(image)
    try:
        _real_export(image, temp)
    except:
        pass
    finally:
        pdb.gimp_image_delete(temp)


register(
    'python-fu-export_x2',
    'Export layers as tgas',
    'Export layers as tgas',
    'Zak',
    'WTFPL',
    '',
    '<Image>/File/Export x2 tgas...',
    '*',
    [],
    [],
    export_x2)

main()