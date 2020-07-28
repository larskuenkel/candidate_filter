import argparse
import reading_cands


def parse_arguments():
    # Parse command line arguments
    parser = argparse.ArgumentParser(description='Command line arguments for the candidate filtering.')
    parser.add_argument('-i', '--input', type=str, default='', metavar=('input_folder'), 
        help="Path to the input files.")
    parser.add_argument('-o', '--output', type=str, default='', metavar=('output_folder'), 
        help="Path of the output folder.")
    args = parser.parse_args()
    return args


def main(args):
    # Main function

    # Read files into a single pandas DataFrame
    df_cands_ini = reading_cands.read_candidate_files(args.input)

    #df_cands_ini.sort_values('snr', inplace=True,ascending=False)

    # Write out candidate list
    df_cands_ini.to_csv(args.output)

if __name__ == "__main__":
    args = parse_arguments()
    main(args)