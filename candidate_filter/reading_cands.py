import pandas as pd
import glob
import xml.etree.ElementTree as ET
from astropy import units as u
from astropy.coordinates import SkyCoord


def read_candidate_files(path, verbose=True):
    # Reads candidates files and include the candidates in a single pandas DataFrame

    files = glob.glob(path + '*/overview.xml')

    if verbose:
        print(f"{len(files)} candidates files found.")


    all_rows = []
    file_index=0
    for file in files:
        tree = ET.parse(file)
        root = tree.getroot()

        # Indexing might break when the candidate files look differently
        candidates = root[6]

        all_rows.extend(create_row(root, candidates, file, file_index))
        file_index+=1

    df_candidates = pd.DataFrame(all_rows)

    # Additional type casting may be necessary or not necessary at all
    df_candidates = df_candidates.astype({"snr": float, "dm": float, "period": float,
        "acc": float})

    if verbose:
        print(f"{len(df_candidates)} candidates read.")

    return df_candidates



def create_row(root, candidates, file, file_index):
    # Read a candidate file and creates data rows

    src_raj = float(root[1].find("src_raj").text)
    src_dej = float(root[1].find("src_dej").text)
    src_rajd, src_dejd = convert_to_deg(src_raj, src_dej)
    rows = []

    # Enter attributes that should be ignored here
    ignored_entries = ['candidate']
    #ignored_entries = ['candidate', 'byte_offset', 'opt_period', 'folded_snr']
    for candidate in candidates:
        new_dict = {}
        for can_entry in candidate.iter():
            if not can_entry.tag in ignored_entries:
                new_dict[can_entry.tag] = can_entry.text
        cand_id = candidate.attrib.get("id")
        new_dict['cand_id'] = cand_id
        new_dict['src_raj'] = src_raj
        new_dict['src_rajd'] = src_rajd
        new_dict['src_dej'] = src_dej
        new_dict['src_dejd'] = src_dejd
        new_dict['file_index'] = file_index
        new_dict['file'] = file
        rows.append(new_dict)
    return rows


def convert_to_deg(ra, dec):
    # Convert hour angle strings to degrees

    ra_string = str(ra)
    ra_string = ra_string[:2] + ' ' + ra_string[2:4] + ' ' + ra_string[4:]
    dec_string = str(dec)
    dec_string = dec_string[:3] + ' ' + dec_string[3:5] + ' ' + dec_string[5:]
    coord = SkyCoord(ra_string + ' ' + dec_string, unit=(u.hourangle, u.deg))
    return coord.ra.deg, coord.dec.deg
