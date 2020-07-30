import argparse
import json
import os
import reading_cands
import cluster_cands
import spatial_rfi
import filtering


def parse_arguments():
    # Parse command line arguments
    parser = argparse.ArgumentParser(
        description='Command line arguments for the candidate filtering.')
    parser.add_argument('-i', '--input', type=str, default='', metavar=('input_files'),
                        help="Path to the input files.", nargs='+')
    parser.add_argument('-o', '--output', type=str, default='', metavar=('output_path'),
                        help="Base name of the output csv files")
    default_config_path = f"{os.path.dirname(__file__)}/default_config.json"
    parser.add_argument('-c', '--config', type=str, default=default_config_path,
                        metavar=('config_file'), help="Path to config file.")
    args = parser.parse_args()
    return args


def main(args):
    # Main function

    # Load config
    with open(args.config) as json_data_file:
        config = json.load(json_data_file)

    # Read files into a single pandas DataFrame
    df_cands_ini, obs_meta_data = reading_cands.read_candidate_files(
        args.input)

    # Create clusters
    df_cands_clustered = cluster_cands.cluster_cand_df(
        df_cands_ini, obs_meta_data, config)

    # Find spatial RFI and write out details about clusters
    df_clusters = spatial_rfi.label_spatial_rfi(df_cands_clustered, config)

    # Label bad clusters
    df_cands_filtered, df_clusters_filtered = filtering.filter_clusters(df_cands_clustered,
                                                                        df_clusters, config)

    # Write out candidate list
    df_cands_filtered.to_csv(f"{args.output}_cands.csv")
    # Write out cluster list
    df_clusters_filtered.to_csv(f"{args.output}_clusters.csv")

    # Write out candidate lists for single beams
    output_folder = f"{os.path.dirname(args.output)}/single_beams/"
    try:
        os.mkdir(output_folder)
    except FileExistsError:
        pass
    unique_file_idxs = df_cands_filtered['file_index']
    for file_index in unique_file_idxs:
        df_file = df_cands_filtered[df_cands_filtered['file_index'] == file_index]
        file_name = os.path.basename(os.path.dirname(df_file['file'].iloc[0]))
        df_file.to_csv(f"{output_folder}{file_name}.csv")


if __name__ == "__main__":
    args = parse_arguments()
    main(args)
