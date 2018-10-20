#!/usr/bin/env python3
import os
import sys
import re

HELP = """
USAGE:  python3 escf.py -o/-l $PATH $NUM -v

-o PATH: Path of the folder with ricc2.out and spectrum
-l PATH: Path of a list file
         The list file should contain:
           - Path of the folder with ricc2.out and spectrum,
           - NAME
         One line for each file, parameters space separated
NUM    : Number of excitations
-v     : Verbose

Result is always in folder of $PATH, as $PATH.csv
"""


# Planck Constant in eV.s
h = 4.135667662e-15

# Speed of Light in nm.s
c = 299792458 * 1e9


def process_file(folder, num, verbose):
    if os.path.isdir(folder):
        file_ricc2 = folder + '/ricc2.out'
        file_spectrum = folder + '/spectrum'
        if os.path.isfile(file_ricc2) and os.path.isfile(file_spectrum):
            with open(file_spectrum, 'r') as f:
                data_spectrum = []
                for x in f.read().split('\n'):
                    if x:
                        if x[0] == '#':
                            data_spectrum = []
                        else:
                            data_spectrum.append(x.split()[1])

            if num > len(data_spectrum):
                num = len(data_spectrum)
                print('No excitation {} and beyond'.format(num))

            with open(file_ricc2, 'r') as f:
                data_ricc2 = f.read()

            data_ricc2 = data_ricc2.partition('Final CC2 energy')[2]

            re_s0 = re.compile('\s(\-?\d+\.\d+)\s')
            s0s = [re_s0.search(data_ricc2).group(1)] * num

            evs = []
            nms = []
            l_mo_trans = []
            l_coeff = []

            data_ricc2 = data_ricc2.partition('%t1')[2]
            data_ricc2 = data_ricc2.partition('eV')[2]
            data_ricc2 = data_ricc2.partition('+')[2]

            for i in range(num):
                for _ in range(5):
                    data_ricc2 = data_ricc2.partition('|')[2]
                re_ev = re.compile('\s(\d+\.\d+([Ee](\-)?\d+)?)\s')
                ev = re_ev.search(data_ricc2).group(1)
                evs.append(ev)

                nms.append(str(h * c / float(ev)))

                data_ricc2 = data_ricc2.partition('\n')[2]

            for i in range(num):
                data_ricc2 = data_ricc2.partition('|amp|     %    |\n')[2]
                data_ricc2 = data_ricc2.partition('\n')[2]
                mo, _, data_ricc2 = data_ricc2.partition('+')

                tmp_mo_trans = []
                tmp_coeff = []

                for x in mo.split('\n'):
                    if len(x) and not x.isspace():
                        x = x.partition('|')[2].strip()
                        re_moi = re.compile('^(\d+)\s')
                        moi = re_moi.search(x).group(1)

                        x = x.partition('|')[2].strip()
                        re_mof = re.compile('^(\d+)\s')

                        mo_trans = (
                            re_mof.search(x).group(1) + '←' + moi
                            )

                        x = (x.strip()[:-1]).strip()
                        re_coef = re.compile('\s(\d+\.\d+)$')

                        coef = re_coef.search(x).group(1)

                        if float(coef) < 10:
                            break

                        tmp_mo_trans.append(mo_trans)
                        tmp_coeff.append(coef)

                l_mo_trans.append((' ' * 5).join(tmp_mo_trans))
                l_coeff.append((' ' * 5).join(tmp_coeff))

            if verbose:
                print()
                print('Singlet up to', num)
                print('  s0:', s0s[0])
                print('  ev:', evs)
                print('  nm:', nms)
                print('  leng:', data_spectrum)
                print('  mo_trans:', l_mo_trans)
                print('  coeff:', l_coeff)

            return [
                ','.join(x)
                for x in zip(s0s, nms, evs, l_mo_trans, data_spectrum, l_coeff)
            ]

        else:
            print('Necessary files do not present in the folder {}!'.format(
                folder
                ))
            print(HELP)
            return False
    else:
        print('Incorrect folder path!')
        print(HELP)
        return False


def main():
    if len(sys.argv) in [4, 5]:
        verbose = False
        if len(sys.argv) == 5:
            if sys.argv[4] == '-v':
                verbose = True
            else:
                print(HELP)
                return

        try:
            num = int(sys.argv[3])
        except ValueError:
            print('Invalid number of excitations!')
            print(HELP)
            return

        if sys.argv[1] == '-o':
            csv = [
                ('S0-Energy,'
                 'Lambda max (nm),'
                 'Energy (eV),'
                 'MO Number,'
                 'Oscilator Strength (length),'
                 'Contribution (%)')
                 ]
            folder = sys.argv[2]
            p = process_file(folder, num, verbose)
            if not p:
                sys.exit()
            csv += p

            with open(folder + '/data.csv', 'w') as f:
                f.write('\n'.join(csv))

        elif sys.argv[1] == '-l':
            csv = [
                ('S0-Energy,'
                 'Name,'
                 'Lambda max (nm),'
                 'Energy (eV),'
                 'MO Number,'
                 'Oscilator Strength (length),'
                 'Contribution (%)')
                 ]
            file_list = sys.argv[2]

            if os.path.isfile(file_list):
                with open(file_list, 'r') as f:
                    files = f.read().split('\n')

                for file_data in files:
                    if file_data and file_data[0] != '#':
                        x = file_data.split()
                        if len(x) != 2:
                            print('Error in List File!')
                            return
                        file, name = x
                        p = process_file(file, num, verbose)
                        if not p:
                            sys.exit()
                        csv += [name + ',' + x for x in p]

                with open(file_list + '.csv', 'w') as wf:
                    wf.write('\n'.join(csv))

        else:
            print(HELP)

    else:
        print(HELP)


if __name__ == '__main__':
    main()