import pandas as pd
import numpy as np


def compare_periods(cand_1, cand_2, obs_length):
        # Quick comparison how many rotations two pulsars make
        # Acceleration is neglected
    period_1 = cand_1.period
    period_2 = cand_2.period

    rotation_difference = abs(obs_length / period_1 - obs_length / period_2)

    return rotation_difference


def broadened_distance(cand_1, cand_2, obs_meta_data):
    # This method broadens the lower period according to the acceleration
    # Due to the weird slope reversal in the candidates this broadening is
    # done based on the absolute acceleration difference

    # cand_1 should have the lower period

    period_1 = cand_1.period
    period_2 = cand_2.period

    acc_1 = cand_1.acc
    acc_2 = cand_2.acc
    delta_abs_acc = abs(acc_2 - acc_1)
    period_1_broadened = acc_upper_range(
        period_1, delta_abs_acc, obs_meta_data["obs_length_over_c"])
    if period_2 > period_1_broadened:
        distance = obs_meta_data["obs_length"] / \
            period_1_broadened - obs_meta_data["obs_length"] / period_2
    else:
        distance = 0

    return distance


def acc_upper_range(period, delta_abs_acc, obs_length_over_c):
    # Increse the period based on the absolute acceleration difference
    return period / (1 - delta_abs_acc * obs_length_over_c)


def relate_candidates(cand_1, cand_2, obs_meta_data, config):
    # Check if two observations should be clustered (no harmonics!)
    dm_distance = abs(cand_2.dm - cand_1.dm)
    if dm_distance < config['max_distance_dm']:
        rot_distance = broadened_distance(cand_1, cand_2, obs_meta_data)
        if rot_distance < config['max_distance_broadened_period']:
            related = True
        else:
            related = False
    else:
        related = False

    return related


def cluster_cand_df(df_cands, obs_meta_data, config):
    # Cluster candidates without harmonics

    # max_distance_broadened_period defines how close related candidates should be after
    # broadening in rotations
    max_distance_broadened_period = config['max_distance_broadened_period']
    # max_distance_period defines how close the periods should be in order
    # for the broadening to be calculated
    max_distance_period = config['max_distance_period']
    # RFI signals can show a broad DM signature, which might require a two-step clustering
    max_distance_dm = config['max_distance_dm']

    # Create DataFrame where period is sorted in order to easier cycle through
    # candidates with similar period
    df_cands_period_sorted = df_cands.sort_values('period', ascending=True)

    cluster_id = 0
    df_cands['cluster_id'] = np.nan
    df_cands_period_sorted['cluster_id'] = np.nan
    df_cands['strongest_in_cluster'] = 0

    # Cycle through all candidates (sorted by snr)
    for snr_index in range(len(df_cands)):
        base_candidate = df_cands.iloc[snr_index]

        # Disregard candidates already in cluster
        if pd.isnull(base_candidate.cluster_id):
            # Create a new cluster
            df_cands.at[snr_index, 'cluster_id'] = cluster_id
            df_cands.at[snr_index, 'strongest_in_cluster'] = 1
            df_cands_period_sorted.at[snr_index, 'cluster_id'] = cluster_id

            # Find position of candidate in the period sorted DataFrame
            period_index = df_cands_period_sorted.index.get_loc(snr_index)

            # Cycle through the periods higher than the base_period
            for period_index_2 in range(period_index, len(df_cands_period_sorted)):
                candidate_2 = df_cands_period_sorted.iloc[period_index_2]

                # Disregard candidates already in cluster
                if pd.isnull(candidate_2.cluster_id):
                    related = relate_candidates(base_candidate, candidate_2,
                                                obs_meta_data, config)

                    if related:
                        df_cands.at[candidate_2.name,
                                    'cluster_id'] = cluster_id
                        df_cands_period_sorted.at[candidate_2.name,
                                                  'cluster_id'] = cluster_id
                    # Break loop when periods are too far from each other
                    # Currently only threshold, could also include max acc
                    else:
                        rot_distance_simple = compare_periods(
                            base_candidate, candidate_2, obs_meta_data["obs_length"])
                        if rot_distance_simple > max_distance_period:
                            break

            # Cycle through the periods lower than the base_period
            for period_index_2 in reversed(range(period_index)):
                candidate_2 = df_cands_period_sorted.iloc[period_index_2]

                # Disregard candidates already in cluster
                if pd.isnull(candidate_2.cluster_id):
                    related = relate_candidates(candidate_2, base_candidate,
                                                obs_meta_data, config)

                    if related:
                        df_cands.at[candidate_2.name,
                                    'cluster_id'] = cluster_id
                        df_cands_period_sorted.at[candidate_2.name,
                                                  'cluster_id'] = cluster_id
                    # Break loop when periods are too far from each other
                    # Currently only threshold, could also include max acc
                    else:
                        rot_distance_simple = compare_periods(
                            base_candidate, candidate_2, obs_meta_data["obs_length"])
                        if rot_distance_simple > max_distance_period:
                            break
            cluster_id += 1

    df_cands = df_cands.astype({"cluster_id": int})
    return df_cands
