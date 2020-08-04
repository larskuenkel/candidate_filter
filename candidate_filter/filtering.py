def filter_clusters(df_cands, df_clusters, config):
    # Filter out bad candidates
    # Creating a class to do the filtering might make things simpler..
    min_decay_value = config['min_spatial_decay']
    min_total_nassoc = config['min_total_nassoc']

    df_cands['spatial_rfi'] = 0
    df_clusters['spatial_rfi'] = 0

    df_cands['low_nassoc'] = 0
    df_clusters['low_nassoc'] = 0

    for (index, cluster) in df_clusters.iterrows():

        cluster_id = cluster['cluster_id']

        # First label spatial RFI
        decay_value = cluster['fit_decay'] + cluster['fit_decay_error']

        if decay_value < min_decay_value:
            df_clusters.loc[cluster.name, 'spatial_rfi'] = 1
            df_cands.loc[df_cands['cluster_id']
                         == cluster_id, 'spatial_rfi'] = 1

        # Label low nassoc:
        total_nassoc = cluster['total_nassoc']
        if total_nassoc < min_total_nassoc:
            df_clusters.loc[cluster.name, 'low_nassoc'] = 1
            df_cands.loc[df_cands['cluster_id']
                         == cluster_id, 'low_nassoc'] = 1

    print(f"Clusters: {len(df_clusters)}")
    print(f"RFI Clusters: {len(df_clusters[df_clusters['spatial_rfi']==1])}")
    print(f"RFI Candidates: {len(df_cands[df_cands['spatial_rfi']==1])}")
    print(f"Low nassoc Candidates: {len(df_cands[df_cands['low_nassoc']==1])}")

    good_files = df_cands[(df_cands['spatial_rfi'] == 0) &
                          (df_cands['low_nassoc'] == 0)]

    # Good files == neither RFI nor low nassoc
    print(f"Good Candidates: {len(good_files)}")
    # Good files to fold == good files which are the strongest in their cluster
    print(
        f"Good Clusters: {len(good_files[good_files['strongest_in_cluster']==1])}")

    return df_cands, df_clusters
