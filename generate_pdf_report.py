#!/usr/bin/env python3

from os.path import join, split, abspath, normpath, dirname
import glob
from datetime import date, datetime
from pprint import pprint

from jinja2.loaders import FileSystemLoader
from latex import build_pdf, escape, LatexBuildError
from latex.jinja2 import make_env

import hong2p.util as u


def clean_generated_latex(latex_str):
    """Returns str w/ any consecutive empty lines removed.
    """
    lines = latex_str.splitlines()
    cleaned_lines = []
    for first, second in zip(lines, lines[1:]):
        if not (first == '' and second == ''):
            cleaned_lines.append(first)
    cleaned_lines.append(lines[-1])
    return '\n'.join(cleaned_lines)


pdfdir = abspath(normpath(join('mix_figs', 'pdf')))
def plot_files_in_order(glob_str):
    """Returns filenames in order for plotting.

    Reverse chronological w/ control following kiwi.
    """
    files = [split(p)[1] for p in glob.glob(join(pdfdir, glob_str))]
    if len(files) == 0:
        return []

    reverse_chronological = True
    control_last = True
    # Since we change sort direction in reverse_chronological case:
    if reverse_chronological:
        control_last = not control_last

    exclude_str = glob_str.replace('*','')
    def file_keys(fname):
        assert fname[-4] == '.', 'following slicing assumes 3 char extension'
        parts = fname[:-4].replace(exclude_str, '').split('_')
        date_part = None
        fly_part = None
        panel_part = None
        for p in parts:
            if p == 'kiwi':
                if panel_part is not None:
                    raise ValueError(
                        f'duplicate panel parts in filename {fname}')

                if control_last:
                    panel_part = 0
                else:
                    panel_part = 1
                continue

            elif p == 'control':
                if panel_part is not None:
                    raise ValueError(
                        f'duplicate panel parts in filename {fname}')

                if control_last:
                    panel_part = 1
                else:
                    panel_part = 0
                continue

            try:
                fly_part_already_found = fly_part is not None
                # TODO also need to support thorimage_id for fly id?
                # just be consistent w/ using num in other analysis?
                fly_part = int(p)
                # Leading zeros might mean this part was actually one of the 
                # "_NNN" format ThorImage IDs. Either way, fly_num should not
                # be formatted into filename with any leading zeros.
                if fly_part != 0 and p[0] == '0':
                    fly_part = None
                else:
                    if fly_part_already_found:
                        # Can't be a ValueError b/c using that as indication
                        # part couldn't be converted to int...
                        raise RuntimeError(
                            f'duplicate fly_num in filename {fname}')
                    continue
            except ValueError:
                pass

            try:
                date_part_already_found = date_part is not None
                date_part = datetime.strptime(p, u.date_fmt_str)
                if date_part_already_found:
                    # Can't be a ValueError b/c using that as indication
                    # part couldn't be converted to a date...
                    raise RuntimeError( f'duplicate date in filename {fname}')
                continue
            except ValueError:
                pass

        if date_part is None:
            raise ValueError('file {} had no date part')
        if fly_part is None:
            raise ValueError('file {} had no fly_num part')
        if panel_part is None:
            raise ValueError('file {} had no panel part')

        return (date_part, fly_part, panel_part)

    # Checking that we have all pairs for all flies.
    # Important since plot layout assumes everything can map to rows of 2
    # elements nicely.
    fname2keys = {f: file_keys(f) for f in files}
    date_fly2seen_panels = dict()
    for f, (date, fly, panel) in fname2keys.items():
        df = (date, fly)
        if df not in date_fly2seen_panels:
            date_fly2seen_panels[df] = {panel}
        else:
            date_fly2seen_panels[df].add(panel)

    p0 = list(date_fly2seen_panels.values())[0]
    for df, seen in date_fly2seen_panels.items():
        if len(seen) != 2 or seen != p0:
            raise ValueError(f'fly {df} did not have all expected panels')


    files = sorted(files, key=lambda f: fname2keys[f])
    if reverse_chronological:
        files = files[::-1]
    return files


def main():
    # TODO pop these out of kwargs if i'm gonna call this from outside,
    # while still keeping this separate module. pass rest of kwargs to rendering
    # fn?
    verbose = False
    only_print_latex = False
    write_latex_for_testing = False

    env = make_env(loader=FileSystemLoader('.'))
    template = env.get_template('template.tex')
    section_names_and_globstrs = [
        ('Threshold sensitivity', 'threshold_sensitivity*'),
        ('Response rates', 'resp_frac_*'),
        ('Response reliability', 'reliable_of_resp_*'),
        ('Normalized mix responder tuning', 'ratio_mix_rel_to_others_*'),
        ('Mix responder tuning', 'mix_rel_to_others_*'),
        #('Correlations', ('c1.svg', 'c2.svg'))
    ]
    # TODO TODO TODO option to use passed in filenames rather than stuff from
    # glob (to only include plots generated in one analysis run, for example)
    # TODO maybe find intersection of globstrs w/ those filenames, and fail
    # if any filenames are passed in w/ unrecognized glob strs
    # might make more sense to just include all passed in actually...
    # but should still group by non-id part of filename (prefix always?)
    # (maybe order by suffix if there are other suffix keys besides
    # date / fly_num / panel??)
    # (put all those in their own section, like at top, for across fly
    # stuff?)
    sections = \
        [(n, plot_files_in_order(gs)) for n, gs in section_names_and_globstrs]

    # TODO if i'm gonna do this, maybe warn about which desired sections
    # were missing plots (or do that regardless...)
    sections = [(name, plots) for name, plots in sections if len(plots) > 0]
    if verbose:
        print('Section names and input files:')
        pprint(sections)
        print('')

    # TODO even if not using sections in latex, maybe include quick list of
    # types of figures to expect at top. maybe even bulleted.

    latex_str = template.render(pdfdir=pdfdir, sections=sections,
        filename_captions=False)
    latex_str = clean_generated_latex(latex_str)

    if write_latex_for_testing:
        tex_fname = 'test.tex'
        print('Writing LaTeX to {} (for testing)'.format(tex_fname))
        with open(tex_fname, 'w') as f:
            f.write(latex_str)

    gen_latex_msg = 'Rendered TeX:\n{}\n'.format(latex_str)
    if only_print_latex or verbose:
        print(gen_latex_msg)
    if only_print_latex:
        import sys; sys.exit()

    current_dir = abspath(dirname(__file__))
    try:
        pdf_fname = (date.today().strftime(u.date_fmt_str) +
            '_kc_mix_analysis.pdf')

        # Current dir needs to be passed so that 'template.tex', and any 
        # other dependencies in current directory, can be accessed in the
        # temporary build dir created by the latex package.
        # The empty string as the last element retains any default search paths
        # TeX builder would have.
        pdf = build_pdf(latex_str, texinputs=[current_dir, ''])
        print('Writing output to {}'.format(pdf_fname))
        pdf.save_to(pdf_fname)

    except LatexBuildError as err:
        if not verbose:
            print(gen_latex_msg)
        raise


if __name__ == '__main__':
    main()

