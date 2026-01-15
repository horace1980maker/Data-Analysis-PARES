"""
Metrics module for Storyline 4.
Computes governance, actor network, dialogue, and conflict metrics.
"""

import logging
import os
from typing import Any, Dict, List, Optional

import numpy as np
import pandas as pd
import yaml

from .config import (
    ACTOR_ID_CANDIDATES,
    ACTOR_NAME_CANDIDATES,
    ACTOR_TYPE_CANDIDATES,
    CONFLICT_CODE_CANDIDATES,
    CONFLICT_DESC_CANDIDATES,
    CONFLICT_LEVEL_CANDIDATES,
    CONFLICT_TYPE_CANDIDATES,
    CONTEXT_ID_COL,
    DIALOGO_NAME_CANDIDATES,
    DIALOGO_SCOPE_CANDIDATES,
    DIALOGO_TYPE_CANDIDATES,
    GEO_ID_COL,
    GRUPO_COL,
    INCIDENCE_CANDIDATES,
    INTEREST_CANDIDATES,
    MDV_ID_CANDIDATES,
    OTHER_ACTOR_CANDIDATES,
    OTHER_ACTOR_NAME_CANDIDATES,
    POWER_CANDIDATES,
    REL_TYPE_CANDIDATES,
    SE_ID_CANDIDATES,
    STRENGTHS_CANDIDATES,
    SUMA_CANDIDATES,
    THREAT_ID_CANDIDATES,
    WEAKNESSES_CANDIDATES,
    YEAR_CANDIDATES,
)
from .transforms import (
    attach_geo,
    canonical_text,
    coerce_numeric,
    explode_text_to_items,
    frequency_table,
    minmax,
    normalize_rel_type,
    pick_first_existing_col,
    safe_group_agg,
)

logger = logging.getLogger(__name__)


def load_params(config_path: str = "config/params.yaml") -> Dict[str, Any]:
    """Load parameters from YAML file."""
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}
    return {}


def build_dim_context_geo(tables: Dict[str, pd.DataFrame]) -> pd.DataFrame:
    """
    Build DIM_CONTEXT_GEO by joining LOOKUP_CONTEXT and LOOKUP_GEO.
    
    Args:
        tables: Dict of loaded tables
        
    Returns:
        Joined dimension table with context_id, grupo, paisaje, admin0, fecha_iso
    """
    ctx = tables.get("LOOKUP_CONTEXT", pd.DataFrame())
    geo = tables.get("LOOKUP_GEO", pd.DataFrame())
    
    if ctx.empty or geo.empty:
        logger.warning("Cannot build DIM_CONTEXT_GEO: missing LOOKUP_CONTEXT or LOOKUP_GEO")
        return pd.DataFrame()
    
    # Find the join column
    ctx_geo_col = pick_first_existing_col(ctx, [GEO_ID_COL, "geo_id", "id_geo"])
    geo_geo_col = pick_first_existing_col(geo, [GEO_ID_COL, "geo_id", "id_geo"])
    
    if not ctx_geo_col or not geo_geo_col:
        logger.warning("Cannot join LOOKUP_CONTEXT to LOOKUP_GEO: missing geo_id column")
        return ctx
    
    # Join
    result = ctx.merge(geo, left_on=ctx_geo_col, right_on=geo_geo_col, how="left", suffixes=("", "_geo"))
    
    # Ensure context_id column
    if CONTEXT_ID_COL not in result.columns:
        ctx_id_col = pick_first_existing_col(result, ["context_id", "id_context", "contexto_id"])
        if ctx_id_col:
            result[CONTEXT_ID_COL] = result[ctx_id_col]
    
    logger.info(f"Built DIM_CONTEXT_GEO with {len(result)} rows")
    return result


def compute_actors_snapshot(
    tables: Dict[str, pd.DataFrame],
    dim_context_geo: pd.DataFrame,
    params: Dict[str, Any],
) -> Dict[str, pd.DataFrame]:
    """
    Compute actor snapshot metrics from TIDY_5_1_ACTORES.
    
    Returns:
        Dict with ACTORS_OVERALL, ACTORS_BY_GRUPO
    """
    outputs = {}
    df = tables.get("TIDY_5_1_ACTORES", pd.DataFrame())
    
    if df.empty:
        logger.warning("TIDY_5_1_ACTORES is empty, skipping actor snapshot")
        return outputs
    
    # Attach geographic info
    df = attach_geo(df, dim_context_geo)
    
    # Find columns
    actor_id_col = pick_first_existing_col(df, ACTOR_ID_CANDIDATES) or "actor_id"
    actor_name_col = pick_first_existing_col(df, ACTOR_NAME_CANDIDATES) or "nombre_actor"
    actor_type_col = pick_first_existing_col(df, ACTOR_TYPE_CANDIDATES)
    power_col = pick_first_existing_col(df, POWER_CANDIDATES)
    interest_col = pick_first_existing_col(df, INTEREST_CANDIDATES)
    
    # Ensure actor_id exists
    if actor_id_col not in df.columns:
        df["actor_id"] = range(len(df))
        actor_id_col = "actor_id"
    
    # Coerce power/interest to numeric
    if power_col:
        df = coerce_numeric(df, [power_col])
    if interest_col:
        df = coerce_numeric(df, [interest_col])
    
    # Build aggregation spec
    base_group = [actor_id_col]
    if actor_name_col and actor_name_col in df.columns:
        base_group.append(actor_name_col)
    if actor_type_col and actor_type_col in df.columns:
        base_group.append(actor_type_col)
    
    agg_spec = {actor_id_col: "count"}
    if power_col and power_col in df.columns:
        agg_spec[power_col] = "mean"
    if interest_col and interest_col in df.columns:
        agg_spec[interest_col] = "mean"
    if GRUPO_COL in df.columns:
        agg_spec[GRUPO_COL] = "nunique"
    
    # ACTORS_OVERALL
    overall = safe_group_agg(df, base_group, agg_spec)
    if not overall.empty:
        # Rename columns for clarity
        rename_map = {}
        for c in overall.columns:
            if "count" in c.lower() or c.endswith("_count"):
                rename_map[c] = "n_mentions"
            elif "nunique" in c.lower() or c.endswith("_nunique"):
                rename_map[c] = "n_groups"
            elif power_col and power_col in c:
                rename_map[c] = "power_mean"
            elif interest_col and interest_col in c:
                rename_map[c] = "interest_mean"
        overall = overall.rename(columns=rename_map)
        outputs["ACTORS_OVERALL"] = overall
        logger.info(f"Computed ACTORS_OVERALL: {len(overall)} actors")
    
    # ACTORS_BY_GRUPO
    if GRUPO_COL in df.columns:
        grupo_group = [GRUPO_COL] + base_group
        agg_spec_grupo = {actor_id_col: "count"}
        if power_col and power_col in df.columns:
            agg_spec_grupo[power_col] = "mean"
        if interest_col and interest_col in df.columns:
            agg_spec_grupo[interest_col] = "mean"
        
        by_grupo = safe_group_agg(df, grupo_group, agg_spec_grupo)
        if not by_grupo.empty:
            rename_map = {}
            for c in by_grupo.columns:
                if "count" in c.lower() or c.endswith("_count"):
                    rename_map[c] = "n_mentions"
                elif power_col and power_col in c:
                    rename_map[c] = "power_mean"
                elif interest_col and interest_col in c:
                    rename_map[c] = "interest_mean"
            by_grupo = by_grupo.rename(columns=rename_map)
            outputs["ACTORS_BY_GRUPO"] = by_grupo
            logger.info(f"Computed ACTORS_BY_GRUPO: {len(by_grupo)} rows")
    
    return outputs


def compute_actor_relations(
    tables: Dict[str, pd.DataFrame],
    dim_context_geo: pd.DataFrame,
    params: Dict[str, Any],
) -> Dict[str, pd.DataFrame]:
    """
    Compute actor relation network metrics from TIDY_5_1_RELACIONES.
    
    Returns:
        Dict with ACTOR_CENTRALITY_OVERALL/BY_GRUPO, DYADS_OVERALL/BY_GRUPO
    """
    outputs = {}
    df = tables.get("TIDY_5_1_RELACIONES", pd.DataFrame())
    
    if df.empty:
        logger.warning("TIDY_5_1_RELACIONES is empty, skipping relation metrics")
        return outputs
    
    # Attach geographic info
    df = attach_geo(df, dim_context_geo)
    
    # Find columns
    actor_id_col = pick_first_existing_col(df, ACTOR_ID_CANDIDATES) or "actor_id"
    other_actor_col = pick_first_existing_col(df, OTHER_ACTOR_CANDIDATES)
    rel_type_col = pick_first_existing_col(df, REL_TYPE_CANDIDATES)
    
    # Ensure actor_id exists
    if actor_id_col not in df.columns:
        logger.warning("No actor_id column found in TIDY_5_1_RELACIONES")
        return outputs
    
    # Normalize relation types
    rel_type_map = params.get("rel_type_map", {})
    if rel_type_col and rel_type_col in df.columns and params.get("normalize_rel_type", True):
        df["rel_type_norm"] = df[rel_type_col].apply(lambda x: normalize_rel_type(x, rel_type_map))
    else:
        df["rel_type_norm"] = "other"
    
    # Compute out-degree (source actor)
    degree_df = df.groupby([actor_id_col, "rel_type_norm"]).size().unstack(fill_value=0)
    degree_df = degree_df.reset_index()
    
    # Rename columns
    rename_cols = {actor_id_col: "actor_id"}
    if "colabora" in degree_df.columns:
        rename_cols["colabora"] = "out_degree_colabora"
    if "conflicto" in degree_df.columns:
        rename_cols["conflicto"] = "out_degree_conflicto"
    if "other" in degree_df.columns:
        rename_cols["other"] = "out_degree_other"
    degree_df = degree_df.rename(columns=rename_cols)
    
    # Total out-degree
    degree_cols = [c for c in degree_df.columns if c.startswith("out_degree_")]
    if degree_cols:
        degree_df["out_degree_total"] = degree_df[degree_cols].sum(axis=1)
    
    # Compute in-degree if other_actor column exists
    if other_actor_col and other_actor_col in df.columns:
        in_degree = df.groupby([other_actor_col, "rel_type_norm"]).size().unstack(fill_value=0)
        in_degree = in_degree.reset_index()
        in_rename = {other_actor_col: "actor_id"}
        if "colabora" in in_degree.columns:
            in_rename["colabora"] = "in_degree_colabora"
        if "conflicto" in in_degree.columns:
            in_rename["conflicto"] = "in_degree_conflicto"
        in_degree = in_degree.rename(columns=in_rename)
        
        # Merge in-degree
        degree_df = degree_df.merge(in_degree, on="actor_id", how="outer").fillna(0)
        
        in_cols = [c for c in degree_df.columns if c.startswith("in_degree_")]
        if in_cols:
            degree_df["in_degree_total"] = degree_df[in_cols].sum(axis=1)
    
    # Join with LOOKUP_ACTOR to get actor_name
    lookup_actor = tables.get("LOOKUP_ACTOR", pd.DataFrame())
    if not lookup_actor.empty:
        actor_id_lookup = pick_first_existing_col(lookup_actor, ACTOR_ID_CANDIDATES) or "actor_id"
        actor_name_lookup = pick_first_existing_col(lookup_actor, ACTOR_NAME_CANDIDATES) or "nombre_actor"
        if actor_id_lookup in lookup_actor.columns and actor_name_lookup in lookup_actor.columns:
            actor_map = lookup_actor[[actor_id_lookup, actor_name_lookup]].drop_duplicates()
            actor_map = actor_map.rename(columns={actor_id_lookup: "actor_id", actor_name_lookup: "actor_name"})
            degree_df = degree_df.merge(actor_map, on="actor_id", how="left")
    
    outputs["ACTOR_CENTRALITY_OVERALL"] = degree_df
    logger.info(f"Computed ACTOR_CENTRALITY_OVERALL: {len(degree_df)} actors")

    
    # ACTOR_CENTRALITY_BY_GRUPO
    if GRUPO_COL in df.columns:
        grupo_degree = df.groupby([GRUPO_COL, actor_id_col, "rel_type_norm"]).size().reset_index(name="count")
        grupo_pivot = grupo_degree.pivot_table(
            index=[GRUPO_COL, actor_id_col],
            columns="rel_type_norm",
            values="count",
            aggfunc="sum",
            fill_value=0
        ).reset_index()
        
        # Rename
        rename_g = {}
        if "colabora" in grupo_pivot.columns:
            rename_g["colabora"] = "out_degree_colabora"
        if "conflicto" in grupo_pivot.columns:
            rename_g["conflicto"] = "out_degree_conflicto"
        grupo_pivot = grupo_pivot.rename(columns=rename_g)
        
        outputs["ACTOR_CENTRALITY_BY_GRUPO"] = grupo_pivot
        logger.info(f"Computed ACTOR_CENTRALITY_BY_GRUPO: {len(grupo_pivot)} rows")
    
    # DYADS_OVERALL
    if other_actor_col and other_actor_col in df.columns:
        dyads = df.groupby([actor_id_col, other_actor_col, "rel_type_norm"]).size().reset_index(name="count")
        outputs["DYADS_OVERALL"] = dyads
        logger.info(f"Computed DYADS_OVERALL: {len(dyads)} dyads")
        
        # DYADS_BY_GRUPO
        if GRUPO_COL in df.columns:
            dyads_grupo = df.groupby([GRUPO_COL, actor_id_col, other_actor_col, "rel_type_norm"]).size().reset_index(name="count")
            outputs["DYADS_BY_GRUPO"] = dyads_grupo
            logger.info(f"Computed DYADS_BY_GRUPO: {len(dyads_grupo)} rows")
    
    return outputs


def compute_dialogue_spaces(
    tables: Dict[str, pd.DataFrame],
    dim_context_geo: pd.DataFrame,
    params: Dict[str, Any],
) -> Dict[str, pd.DataFrame]:
    """
    Compute dialogue spaces and participation metrics.
    
    Returns:
        Dict with DIALOGUE_SPACES_*, DIALOGUE_PARTICIPATION_*, ACTOR_IN_SPACES_*
    """
    outputs = {}
    dialogo = tables.get("TIDY_5_2_DIALOGO", pd.DataFrame())
    dialogo_actor = tables.get("TIDY_5_2_DIALOGO_ACTOR", pd.DataFrame())
    
    if dialogo.empty:
        logger.warning("TIDY_5_2_DIALOGO is empty, skipping dialogue metrics")
        return outputs
    
    # Attach geographic info
    dialogo = attach_geo(dialogo, dim_context_geo)
    
    # Find columns
    dialogo_id_col = pick_first_existing_col(dialogo, ["dialogo_id", "id_dialogo", "espacio_id"]) or "dialogo_id"
    name_col = pick_first_existing_col(dialogo, DIALOGO_NAME_CANDIDATES)
    type_col = pick_first_existing_col(dialogo, DIALOGO_TYPE_CANDIDATES)
    scope_col = pick_first_existing_col(dialogo, DIALOGO_SCOPE_CANDIDATES)
    strengths_col = pick_first_existing_col(dialogo, STRENGTHS_CANDIDATES)
    weaknesses_col = pick_first_existing_col(dialogo, WEAKNESSES_CANDIDATES)
    
    # DIALOGUE_SPACES_OVERALL
    group_cols = []
    if name_col and name_col in dialogo.columns:
        group_cols.append(name_col)
    if type_col and type_col in dialogo.columns:
        group_cols.append(type_col)
    if scope_col and scope_col in dialogo.columns:
        group_cols.append(scope_col)
    
    if group_cols:
        spaces_overall = dialogo.groupby(group_cols).size().reset_index(name="n_records")
        outputs["DIALOGUE_SPACES_OVERALL"] = spaces_overall
        logger.info(f"Computed DIALOGUE_SPACES_OVERALL: {len(spaces_overall)} spaces")
        
        # DIALOGUE_SPACES_BY_GRUPO
        if GRUPO_COL in dialogo.columns:
            grupo_group = [GRUPO_COL] + group_cols
            spaces_grupo = dialogo.groupby(grupo_group).size().reset_index(name="n_records")
            outputs["DIALOGUE_SPACES_BY_GRUPO"] = spaces_grupo
            logger.info(f"Computed DIALOGUE_SPACES_BY_GRUPO: {len(spaces_grupo)} rows")
    
    # Process participation if DIALOGO_ACTOR exists
    if not dialogo_actor.empty:
        da_dialogo_id = pick_first_existing_col(dialogo_actor, ["dialogo_id", "id_dialogo", "espacio_id"])
        da_actor_id = pick_first_existing_col(dialogo_actor, ACTOR_ID_CANDIDATES)
        
        if da_dialogo_id and da_dialogo_id in dialogo_actor.columns:
            # DIALOGUE_PARTICIPATION: per dialogo, count actors
            participation = dialogo_actor.groupby(da_dialogo_id).agg(
                n_actors=(da_actor_id, "nunique") if da_actor_id else (da_dialogo_id, "count")
            ).reset_index()
            
            # Join with DIALOGO names
            if not participation.empty and not dialogo.empty:
                if dialogo_id_col and dialogo_id_col in dialogo.columns and name_col and name_col in dialogo.columns:
                    names_map = dialogo[[dialogo_id_col, name_col]].drop_duplicates()
                    participation = participation.merge(
                        names_map, 
                        left_on=da_dialogo_id, 
                        right_on=dialogo_id_col, 
                        how="left"
                    )
            
            outputs["DIALOGUE_PARTICIPATION_OVERALL"] = participation
            logger.info(f"Computed DIALOGUE_PARTICIPATION_OVERALL: {len(participation)} spaces")
            
            # ACTOR_IN_SPACES: per actor, count spaces
            if da_actor_id and da_actor_id in dialogo_actor.columns:
                actor_spaces = dialogo_actor.groupby(da_actor_id).agg(
                    n_spaces=(da_dialogo_id, "nunique")
                ).reset_index()
                
                # Join with ACTOR names from LOOKUP_ACTOR
                lookup_actor = tables.get("LOOKUP_ACTOR", pd.DataFrame())
                if not actor_spaces.empty and not lookup_actor.empty:
                    la_id = pick_first_existing_col(lookup_actor, ACTOR_ID_CANDIDATES)
                    la_name = pick_first_existing_col(lookup_actor, ACTOR_NAME_CANDIDATES)
                    
                    if la_id and la_id in lookup_actor.columns and la_name and la_name in lookup_actor.columns:
                        actor_names_map = lookup_actor[[la_id, la_name]].drop_duplicates()
                        actor_spaces = actor_spaces.merge(
                            actor_names_map,
                            left_on=da_actor_id,
                            right_on=la_id,
                            how="left"
                        )
                
                outputs["ACTOR_IN_SPACES_OVERALL"] = actor_spaces
                logger.info(f"Computed ACTOR_IN_SPACES_OVERALL: {len(actor_spaces)} actors")
    
    # Strengths/weaknesses frequency (optional)
    if strengths_col and strengths_col in dialogo.columns:
        strengths_items = dialogo[strengths_col].dropna().apply(
            lambda x: explode_text_to_items(x, min_len=params.get("min_text_len", 2))
        )
        freq = frequency_table(strengths_items, params.get("top_n", 20))
        if not freq.empty:
            outputs["DIALOGUE_STRENGTHS_FREQ_OVERALL"] = freq
    
    if weaknesses_col and weaknesses_col in dialogo.columns:
        weaknesses_items = dialogo[weaknesses_col].dropna().apply(
            lambda x: explode_text_to_items(x, min_len=params.get("min_text_len", 2))
        )
        freq = frequency_table(weaknesses_items, params.get("top_n", 20))
        if not freq.empty:
            outputs["DIALOGUE_WEAKNESSES_FREQ_OVERALL"] = freq
    
    return outputs


def compute_conflicts_profile(
    tables: Dict[str, pd.DataFrame],
    dim_context_geo: pd.DataFrame,
    params: Dict[str, Any],
) -> Dict[str, pd.DataFrame]:
    """
    Compute conflict profile metrics from TIDY_6_1 and TIDY_6_2.
    
    Returns:
        Dict with CONFLICTS_*, CONFLICT_TIMELINE_*, CONFLICT_ACTORS_*
    """
    outputs = {}
    events = tables.get("TIDY_6_1_CONFLICT_EVENTS", pd.DataFrame())
    actors = tables.get("TIDY_6_2_CONFLICTO_ACTOR", pd.DataFrame())
    
    if events.empty:
        logger.warning("TIDY_6_1_CONFLICT_EVENTS is empty, skipping conflict metrics")
        return outputs
    
    # Attach geographic info if context_id exists
    events = attach_geo(events, dim_context_geo)
    
    # Find columns
    conflict_code_col = pick_first_existing_col(events, CONFLICT_CODE_CANDIDATES)
    type_col = pick_first_existing_col(events, CONFLICT_TYPE_CANDIDATES)
    level_col = pick_first_existing_col(events, CONFLICT_LEVEL_CANDIDATES)
    year_col = pick_first_existing_col(events, YEAR_CANDIDATES)
    incidence_col = pick_first_existing_col(events, INCIDENCE_CANDIDATES)
    
    # Coerce numeric columns
    if year_col:
        events = coerce_numeric(events, [year_col])
    if incidence_col:
        events = coerce_numeric(events, [incidence_col])
    
    # CONFLICTS_OVERALL: group by conflict code
    if conflict_code_col and conflict_code_col in events.columns:
        group_cols = [conflict_code_col]
        if type_col and type_col in events.columns:
            group_cols.append(type_col)
        if level_col and level_col in events.columns:
            group_cols.append(level_col)
        
        agg_dict = {conflict_code_col: "count"}
        if year_col and year_col in events.columns:
            agg_dict[year_col] = ["min", "max"]
        if incidence_col and incidence_col in events.columns:
            agg_dict[incidence_col] = "mean"
        
        try:
            # Separate count from other aggregations to avoid KeyError on grouping column
            agg_dict = {}
            if year_col and year_col in events.columns:
                agg_dict[year_col] = ["min", "max"]
            if incidence_col and incidence_col in events.columns:
                agg_dict[incidence_col] = "mean"
            
            # Compute aggregations (if any)
            if agg_dict:
                conflicts_agg = events.groupby(group_cols, as_index=False).agg(agg_dict)
                # Flatten columns
                if isinstance(conflicts_agg.columns, pd.MultiIndex):
                    conflicts_agg.columns = [
                        "_".join(filter(None, map(str, col))).strip("_")
                        for col in conflicts_agg.columns
                    ]
            else:
                conflicts_agg = pd.DataFrame(columns=group_cols)
            
            # Compute counts using size()
            conflicts_counts = events.groupby(group_cols, as_index=False).size()
            conflicts_counts = conflicts_counts.rename(columns={"size": "n_events"})
            
            # Merge
            if not conflicts_agg.empty:
                conflicts_overall = conflicts_counts.merge(conflicts_agg, on=group_cols, how="left")
            else:
                conflicts_overall = conflicts_counts

            # Rename for clarity
            rename_map = {}
            for c in conflicts_overall.columns:
                if "min" in c.lower() and year_col and year_col in c:
                    rename_map[c] = "first_year"
                elif "max" in c.lower() and year_col and year_col in c:
                    rename_map[c] = "last_year"
                elif "mean" in c.lower() and incidence_col and incidence_col in c:
                    rename_map[c] = "mean_incidence"
            conflicts_overall = conflicts_overall.rename(columns=rename_map)
            
            # Join with LOOKUP_CONFLICTO to get conflict descriptions
            lookup_conflicto = tables.get("LOOKUP_CONFLICTO", pd.DataFrame())
            if not lookup_conflicto.empty and conflict_code_col:
                conflict_id_lookup = pick_first_existing_col(lookup_conflicto, CONFLICT_CODE_CANDIDATES) or "conflicto_id"
                conflict_desc_lookup = pick_first_existing_col(lookup_conflicto, CONFLICT_DESC_CANDIDATES) or "descripcion"
                if conflict_id_lookup in lookup_conflicto.columns:
                    conflict_map_cols = [conflict_id_lookup]
                    if conflict_desc_lookup and conflict_desc_lookup in lookup_conflicto.columns:
                        conflict_map_cols.append(conflict_desc_lookup)
                    conflict_map = lookup_conflicto[conflict_map_cols].drop_duplicates()
                    rename_dict = {conflict_id_lookup: conflict_code_col}
                    if conflict_desc_lookup in conflict_map.columns:
                        rename_dict[conflict_desc_lookup] = "conflict_description"
                    conflict_map = conflict_map.rename(columns=rename_dict)
                    conflicts_overall = conflicts_overall.merge(conflict_map, on=conflict_code_col, how="left")
            
            outputs["CONFLICTS_OVERALL"] = conflicts_overall
            logger.info(f"Computed CONFLICTS_OVERALL: {len(conflicts_overall)} conflicts")
        except Exception as e:
            logger.error(f"Failed to compute CONFLICTS_OVERALL: {e}", exc_info=True)

        
        # CONFLICTS_BY_GRUPO
        if GRUPO_COL in events.columns and conflict_code_col and conflict_code_col in events.columns:
            try:
                grupo_group = [GRUPO_COL] + group_cols
                conflicts_grupo = events.groupby(grupo_group, as_index=False).size()
                conflicts_grupo = conflicts_grupo.rename(columns={"size": "n_events"})
                outputs["CONFLICTS_BY_GRUPO"] = conflicts_grupo
                logger.info(f"Computed CONFLICTS_BY_GRUPO: {len(conflicts_grupo)} rows")
            except Exception as e:
                logger.error(f"Failed to compute CONFLICTS_BY_GRUPO: {e}", exc_info=True)
    
    # CONFLICT_TIMELINE_OVERALL: group by year
    if year_col and year_col in events.columns:
        timeline = events.groupby(year_col, as_index=False).agg({
            year_col: "count"
        }).rename(columns={year_col: "n_events"})
        timeline = timeline.rename(columns={f"{year_col}_count": "n_events"} if f"{year_col}_count" in timeline.columns else {})
        
        # Actually we need to re-do this properly
        timeline = events.groupby(year_col).size().reset_index(name="n_events")
        timeline = timeline.rename(columns={year_col: "year"})
        
        if incidence_col and incidence_col in events.columns:
            incidence_by_year = events.groupby(year_col)[incidence_col].mean().reset_index()
            incidence_by_year.columns = ["year", "mean_incidence"]
            timeline = timeline.merge(incidence_by_year, on="year", how="left")
        
        outputs["CONFLICT_TIMELINE_OVERALL"] = timeline
        logger.info(f"Computed CONFLICT_TIMELINE_OVERALL: {len(timeline)} years")
        
        # CONFLICT_TIMELINE_BY_GRUPO
        if GRUPO_COL in events.columns:
            timeline_grupo = events.groupby([GRUPO_COL, year_col]).size().reset_index(name="n_events")
            timeline_grupo = timeline_grupo.rename(columns={year_col: "year"})
            outputs["CONFLICT_TIMELINE_BY_GRUPO"] = timeline_grupo
            logger.info(f"Computed CONFLICT_TIMELINE_BY_GRUPO: {len(timeline_grupo)} rows")
    
    # CONFLICT_ACTORS_OVERALL from TIDY_6_2
    if not actors.empty:
        ca_conflict_col = pick_first_existing_col(actors, CONFLICT_CODE_CANDIDATES)
        ca_actor_col = pick_first_existing_col(actors, ACTOR_ID_CANDIDATES + ACTOR_NAME_CANDIDATES)
        
        if ca_conflict_col and ca_conflict_col in actors.columns and ca_actor_col and ca_actor_col in actors.columns:
            conflict_actors = actors.groupby([ca_conflict_col, ca_actor_col]).size().reset_index(name="n_records")
            
            # Join with LOOKUP_CONFLICTO for descriptions
            lookup_conflicto = tables.get("LOOKUP_CONFLICTO", pd.DataFrame())
            if not lookup_conflicto.empty:
                # Find columns in lookup
                lc_id = pick_first_existing_col(lookup_conflicto, CONFLICT_CODE_CANDIDATES) or "conflicto_id"
                lc_desc = pick_first_existing_col(lookup_conflicto, CONFLICT_DESC_CANDIDATES) or "descripcion"
                
                if lc_id in lookup_conflicto.columns and lc_desc in lookup_conflicto.columns:
                    c_map = lookup_conflicto[[lc_id, lc_desc]].drop_duplicates()
                    # Rename for merge if needed
                    c_map = c_map.rename(columns={lc_id: ca_conflict_col, lc_desc: "conflict_description"})
                    conflict_actors = conflict_actors.merge(c_map, on=ca_conflict_col, how="left")

            # Join with LOOKUP_ACTOR for actor names
            lookup_actor = tables.get("LOOKUP_ACTOR", pd.DataFrame())
            if not lookup_actor.empty:
                la_id = pick_first_existing_col(lookup_actor, ACTOR_ID_CANDIDATES) or "actor_id"
                la_name = pick_first_existing_col(lookup_actor, ACTOR_NAME_CANDIDATES) or "nombre_actor"
                
                if la_id in lookup_actor.columns and la_name in lookup_actor.columns:
                    a_map = lookup_actor[[la_id, la_name]].drop_duplicates()
                    a_map = a_map.rename(columns={la_id: ca_actor_col, la_name: "actor_name"})
                    conflict_actors = conflict_actors.merge(a_map, on=ca_actor_col, how="left")

            outputs["CONFLICT_ACTORS_OVERALL"] = conflict_actors
            logger.info(f"Computed CONFLICT_ACTORS_OVERALL: {len(conflict_actors)} rows")
        else:
            logger.warning(f"Skipping CONFLICT_ACTORS: conflict_col={ca_conflict_col}, actor_col={ca_actor_col}, available={list(actors.columns)}")

    
    return outputs


def compute_linkages(
    tables: Dict[str, pd.DataFrame],
    dim_context_geo: pd.DataFrame,
    params: Dict[str, Any],
) -> Dict[str, pd.DataFrame]:
    """
    Compute conflict linkages to threats/services/livelihoods.
    
    Returns:
        Dict with LINK_* tables
    """
    outputs = {}
    mapeo_mdv = tables.get("TIDY_4_2_1_MAPEO_CONFLICTO", pd.DataFrame())
    mapeo_se = tables.get("TIDY_4_2_2_MAPEO_CONFLICTO", pd.DataFrame())
    
    # Process MDV-threat-conflict linkages
    if not mapeo_mdv.empty:
        logger.info(f"Processing MAPEO_CONFLICTO MDV with columns: {list(mapeo_mdv.columns)}")
        mapeo_mdv = attach_geo(mapeo_mdv, dim_context_geo)
        
        conflict_col = pick_first_existing_col(mapeo_mdv, CONFLICT_CODE_CANDIDATES)
        threat_col = pick_first_existing_col(mapeo_mdv, THREAT_ID_CANDIDATES)
        
        logger.info(f"Linkages MDV - conflict_col: {conflict_col}, threat_col: {threat_col}")
        
        if conflict_col and conflict_col in mapeo_mdv.columns and threat_col and threat_col in mapeo_mdv.columns:
            # Use only unique columns for grouping
            group_cols = list(dict.fromkeys([conflict_col, threat_col]))
            
            link_mdv = mapeo_mdv.groupby(group_cols).size().reset_index(name="n_links")
            outputs["LINK_MDV_THREAT_CONFLICT_OVERALL"] = link_mdv
            logger.info(f"Computed LINK_MDV_THREAT_CONFLICT_OVERALL: {len(link_mdv)} links")
            
            # Top threats linked to conflicts
            if threat_col in mapeo_mdv.columns:
                top_threats = mapeo_mdv.groupby(threat_col).size().reset_index(name="n_conflict_links")
                top_threats = top_threats.sort_values("n_conflict_links", ascending=False)
                outputs["TOP_CONFLICT_LINKED_THREATS"] = top_threats.head(params.get("top_n", 10))
    
    # Process SE-threat-conflict linkages
    if not mapeo_se.empty:
        logger.info(f"Processing MAPEO_CONFLICTO SE with columns: {list(mapeo_se.columns)}")
        mapeo_se = attach_geo(mapeo_se, dim_context_geo)
        
        conflict_col = pick_first_existing_col(mapeo_se, CONFLICT_CODE_CANDIDATES)
        threat_col = pick_first_existing_col(mapeo_se, THREAT_ID_CANDIDATES)
        
        logger.info(f"Linkages SE - conflict_col: {conflict_col}, threat_col: {threat_col}")
        
        if conflict_col and conflict_col in mapeo_se.columns and threat_col and threat_col in mapeo_se.columns:
            # Use only unique columns for grouping
            group_cols = list(dict.fromkeys([conflict_col, threat_col]))
            
            link_se = mapeo_se.groupby(group_cols).size().reset_index(name="n_links")
            outputs["LINK_SE_THREAT_CONFLICT_OVERALL"] = link_se
            logger.info(f"Computed LINK_SE_THREAT_CONFLICT_OVERALL: {len(link_se)} links")
    
    return outputs


def compute_feasibility_index(
    metrics: Dict[str, pd.DataFrame],
    params: Dict[str, Any],
) -> Dict[str, pd.DataFrame]:
    """
    Compute feasibility diagnostic index.
    
    Combines:
    - Actor network strength (from collaboration degree)
    - Dialogue coverage (from participation)
    - Conflict risk (from conflict events)
    
    Returns:
        Dict with FEASIBILITY_OVERALL, FEASIBILITY_BY_GRUPO
    """
    outputs = {}
    
    w1 = params.get("w_actor_network_strength", 0.35)
    w2 = params.get("w_dialogue_coverage", 0.25)
    w3 = params.get("w_conflict_risk", 0.40)
    fill_missing = params.get("fill_missing_norm", 0.5)
    
    # Get component data
    centrality = metrics.get("ACTOR_CENTRALITY_BY_GRUPO", pd.DataFrame())
    participation = metrics.get("DIALOGUE_PARTICIPATION_OVERALL", pd.DataFrame())
    timeline_grupo = metrics.get("CONFLICT_TIMELINE_BY_GRUPO", pd.DataFrame())
    
    # If we have by-grupo data, compute feasibility by grupo
    if not centrality.empty and GRUPO_COL in centrality.columns:
        grupos = centrality[GRUPO_COL].unique()
        
        feas_data = []
        for grupo in grupos:
            row = {"grupo": grupo}
            
            # Actor network strength: mean collaboration degree
            grupo_cent = centrality[centrality[GRUPO_COL] == grupo]
            if "out_degree_colabora" in grupo_cent.columns and len(grupo_cent) > 0:
                row["actor_network_strength"] = grupo_cent["out_degree_colabora"].mean()
            else:
                row["actor_network_strength"] = 0
            
            # Dialogue coverage: n_actors in participation (simplified)
            if not participation.empty and "n_actors" in participation.columns:
                row["dialogue_coverage"] = participation["n_actors"].mean()
            else:
                row["dialogue_coverage"] = 0
            
            # Conflict risk: n_events from timeline
            if not timeline_grupo.empty and GRUPO_COL in timeline_grupo.columns:
                grupo_timeline = timeline_grupo[timeline_grupo[GRUPO_COL] == grupo]
                if "n_events" in grupo_timeline.columns and len(grupo_timeline) > 0:
                    row["conflict_events"] = grupo_timeline["n_events"].sum()
                else:
                    row["conflict_events"] = 0
            else:
                row["conflict_events"] = 0
            
            feas_data.append(row)
        
        if feas_data:
            feas_df = pd.DataFrame(feas_data)
            
            # Normalize components
            feas_df["actor_strength_norm"] = minmax(feas_df["actor_network_strength"])
            feas_df["dialogue_norm"] = minmax(feas_df["dialogue_coverage"])
            feas_df["conflict_risk_norm"] = minmax(feas_df["conflict_events"])
            
            # Compute feasibility: higher actor strength + higher dialogue - higher conflict
            feas_df["feasibility_score"] = (
                w1 * feas_df["actor_strength_norm"] +
                w2 * feas_df["dialogue_norm"] +
                w3 * (1 - feas_df["conflict_risk_norm"])
            )
            
            outputs["FEASIBILITY_BY_GRUPO"] = feas_df
            logger.info(f"Computed FEASIBILITY_BY_GRUPO: {len(feas_df)} grupos")
            
            # Overall: mean across grupos
            overall = pd.DataFrame([{
                "scope": "overall",
                "actor_strength_norm": feas_df["actor_strength_norm"].mean(),
                "dialogue_norm": feas_df["dialogue_norm"].mean(),
                "conflict_risk_norm": feas_df["conflict_risk_norm"].mean(),
                "feasibility_score": feas_df["feasibility_score"].mean(),
            }])
            outputs["FEASIBILITY_OVERALL"] = overall
    
    return outputs


def process_metrics(
    tables: Dict[str, pd.DataFrame],
    params: Dict[str, Any],
) -> Dict[str, pd.DataFrame]:
    """
    Main orchestration for all metric computation.
    
    Args:
        tables: Dict of loaded tables
        params: Pipeline parameters
        
    Returns:
        Dict of all computed metrics tables
    """
    metrics = {}
    
    # Build dimension table
    dim_context_geo = build_dim_context_geo(tables)
    if not dim_context_geo.empty:
        metrics["DIM_CONTEXT_GEO"] = dim_context_geo
    
    # Compute actors snapshot
    actors_metrics = compute_actors_snapshot(tables, dim_context_geo, params)
    metrics.update(actors_metrics)
    
    # Compute actor relations
    relations_metrics = compute_actor_relations(tables, dim_context_geo, params)
    metrics.update(relations_metrics)
    
    # Compute dialogue spaces
    dialogue_metrics = compute_dialogue_spaces(tables, dim_context_geo, params)
    metrics.update(dialogue_metrics)
    
    # Compute conflicts profile
    conflict_metrics = compute_conflicts_profile(tables, dim_context_geo, params)
    metrics.update(conflict_metrics)
    
    # Compute linkages
    linkage_metrics = compute_linkages(tables, dim_context_geo, params)
    metrics.update(linkage_metrics)
    
    # Compute feasibility index
    feasibility_metrics = compute_feasibility_index(metrics, params)
    metrics.update(feasibility_metrics)
    
    logger.info(f"Total metrics tables computed: {len(metrics)}")
    return metrics
