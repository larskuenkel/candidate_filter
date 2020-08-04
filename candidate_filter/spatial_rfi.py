import numpy as np
import math
from sklearn.metrics import pairwise_distances
from scipy.optimize import curve_fit
import pandas as pd
import os
import matplotlib.pyplot as plt


def angular_distance(degree_1, degree_2):
    # Calculate angular distance in arcminutes
    if not (degree_1 == degree_2).all():
        degree_1_rad = degree_1 / 360 * 2 * math.pi
        degree_2_rad = degree_2 / 360 * 2 * math.pi
        angular_distance_rad = math.acos(math.sin(degree_1[1]) * math.sin(degree_2[1]) + math.cos(
            degree_1[1]) * math.cos(degree_2[1]) * math.cos(degree_1[0] - degree_2[0]))
        angular_distance_arcmin = angular_distance_rad * \
            360 / (2 * math.pi) * 60
    else:
        angular_distance_arcmin = 0
    return angular_distance_arcmin


def decay_law(x, a, b):
    return a * np.exp(-b * x)


def fit_decay(x_vals, y_vals):
    # ,method='trf',loss='arctan')
    popt, pcov = curve_fit(decay_law, x_vals, y_vals, p0=[y_vals.max(), 0.01])
    errors = np.sqrt(np.diag(pcov))
    return popt, errors


def label_spatial_rfi(df_cands, config, plot_arguments=[False, '']):
    # Determine if the clusters show RFI like behaviour spatially

    # Count size oif cluster and order them, could be later be replaced
    # when DataFrame containing the data about the cluster is created
    unique, counts = np.unique(df_cands['cluster_id'], return_counts=True)
    count_sort_ind = np.argsort(-counts)
    unique = unique[count_sort_ind]
    counts = counts[count_sort_ind]

    if plot_arguments[0]:
        try:
            os.mkdir(plot_arguments[1])
        except FileExistsError:
            pass

    # Create list that contains the new cluster DataFrame
    rows = []

    # Cycle thorugh all clusters, beginning with the largest
    for i in unique[:]:
        # Create DataFrame with only the cluster candidates
        df_truncated = df_cands[df_cands['cluster_id'] == i]

        # First read out some basic values
        best_candidate = df_truncated.iloc[0]
        new_row = {}
        new_row['cluster_id'] = i
        new_row['cluster_size'] = len(df_truncated)
        new_row['cluster_beams'] = df_truncated['file_index'].nunique()
        new_row['max_snr'] = df_truncated['snr'].max()
        new_row['min_snr'] = df_truncated['snr'].min()
        new_row['best_candidate_index'] = best_candidate.name
        new_row['best_candidate_file'] = best_candidate['file']
        new_row['best_period'] = best_candidate['period']
        new_row['best_acc'] = best_candidate['acc']
        new_row['best_dm'] = best_candidate['dm']
        new_row['max_dm'] = df_truncated['dm'].max()
        new_row['min_dm'] = df_truncated['dm'].min()
        new_row['period_range'] = df_truncated['period'].max() - \
            df_truncated['period'].min()

        total_nassoc = len(df_truncated) + df_truncated['nassoc'].sum()

        new_row['total_nassoc'] = total_nassoc

        # Create DataFrame with only the strongest candidate per beam
        unique_beams = df_truncated['file_index'].unique()
        df_beams = pd.DataFrame([])
        for beam in unique_beams:
            # When the same beam is in multiple files this does not quite correctly
            row = df_truncated[df_truncated['file_index'] == beam].iloc[0]
            df_beams = df_beams.append(row, ignore_index=True)

        # Fit an exponential decay to the maximum snr in each beam where a candidate is seen
        coords = df_beams[['src_rajd', 'src_dejd']].values

        if len(df_beams) > 1:

            # Currently calculates all distances, not fast, but gives largest value
            distances = pairwise_distances(coords, metric=angular_distance)

            try:
                max_distance = distances[distances > 0].max()
                min_distance = distances[distances > 0].min()
            except:
                max_distance = np.nan
                min_distance = np.nan
            if len(df_beams) > config['min_size_cluster_for_fit']:
                max_pos = df_beams['snr'].values.argmax()
                distances_from_max = distances[max_pos, :]
                snr_vals = df_beams['snr'].values
                try:
                    fit_parameters, fit_errors = fit_decay(
                        distances_from_max, snr_vals)
                except:
                    fit_parameters, fit_errors = [
                        np.nan, np.nan], [np.nan, np.nan]
                fitted = True
            else:
                fit_parameters, fit_errors = [np.nan, np.nan], [np.nan, np.nan]
                fitted = False
        else:
            max_distance = np.nan
            min_distance = np.nan
            fitted = False

        new_row['max_distance'] = max_distance
        new_row['min_distance'] = min_distance
        new_row['fit_decay'] = fit_parameters[1]
        new_row['fit_decay_error'] = fit_errors[1]
        new_row['fit_amplitude'] = fit_parameters[0]
        new_row['fit_amplitude_error'] = fit_errors[0]

        rows.append(new_row)

        if plot_arguments[0] and fitted:
            # Plot diagnostic plots
            fig, (ax1, ax2, ax3, ax4) = plt.subplots(1, 4, figsize=(25, 4))

            ax1.scatter(df_beams['src_rajd'],
                        df_beams['src_dejd'], s=df_beams['snr'] * 1.5)
            ax1.set_xlim(df_cands['src_rajd'].min() - 0.01,
                         df_cands['src_rajd'].max() + 0.01)
            ax1.set_ylim(df_cands['src_dejd'].min() - 0.01,
                         df_cands['src_dejd'].max() + 0.01)
            ax1.set(xlabel='src_rajd', ylabel='src_dejd')
            ax1.set_title(f"{new_row['cluster_size']} candidates in {new_row['cluster_beams']} beams")

            if len(snr_vals) > 3:
                new_xvals = np.linspace(0, distances_from_max.max(), 20)
                new_yvals = decay_law(new_xvals, *fit_parameters)
                ax2.plot(new_xvals, new_yvals)
            ax2.scatter(distances_from_max, snr_vals)
            ax2.set_title(f"a*exp(-b*x); b={fit_parameters[1]}")
            ax2.set(xlabel='Distance (´)', ylabel='snr')

            ax3.scatter(df_cands['period'], df_cands['acc'],
                        s=df_cands['snr'] * 2, c='r')
            ax3.scatter(
                df_truncated['period'], df_truncated['acc'], s=df_truncated['snr'] * 2)
            border = (df_truncated['period'].max() -
                      df_truncated['period'].min()) * 0.1
            if border == 0:
                border = new_row['best_period'] * 0.02
            ax3.set_xlim(df_truncated['period'].min(
            ) - border, df_truncated['period'].max() + border)
            ax3.set(xlabel='period', ylabel='acc')
            ax3.set_title(f"P0:  {new_row['best_period']}; Range: {new_row['period_range']}")

            ax4.scatter(df_truncated['period'],
                        df_truncated['dm'], s=df_truncated['snr'] * 2)
            ax4.set_xlim(df_truncated['period'].min(
            ) - border, df_truncated['period'].max() + border)
            ax4.set(xlabel='period', ylabel='DM')
            ax4.set_title(f"DM: {new_row['min_dm']} - {new_row['max_dm']}")

            plt.savefig(f"{plot_arguments[1]}cluster_{i}_Size_{new_row['cluster_size']}_P0_{new_row['best_period']}.png",
                        bbox_inches='tight')
    df_clusters = pd.DataFrame(rows)

    return df_clusters
