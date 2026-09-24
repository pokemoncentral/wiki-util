drop view if exists type;
create view type as
select t.*, tn.name as it_name
from pokemon_v2_type t
    join pokemon_v2_typename tn on tn.type_id = t.id
where
    tn.language_id = (
        select id
        from pokemon_v2_language
        where iso3166 = 'it'
        limit 1
    );

drop view if exists pkmn;
create view pkmn as
with pkmn_type as (
    select
        j.id,
        j.type_id,
        j.pokemon_id,
        j.slot,
        t.name,
        t.it_name
    from pokemon_v2_pokemontype j
        join type t on t.id = j.type_id
),
pkmn_names as (
    select ps.id, pn.name
    from pokemon_v2_pokemonspeciesname ps
        join pokemon_v2_pokemonspeciesname pn on pn.pokemon_species_id = ps.id
    where
        pn.language_id = (
            select id
            from pokemon_v2_language
            where iso3166 = 'it'
            limit 1
        )
),
egg_group_names as (
    select eg.id, en.name as it_name
    from pokemon_v2_pokemonegggroup eg
        join pokemon_v2_egggroupname en on en.egg_group_id = eg.id
    where
        en.language_id = (
            select id
            from pokemon_v2_language
            where iso3166 = 'it'
            limit 1
        )
    )
select
    p.id as id,
    pn.name as name,
    t1.it_name as type1,
    t2.it_name as type2,
    (
        select en.it_name
        from pokemon_v2_pokemonegggroup egj
            join egg_group_names en on en.id = egj.egg_group_id
        where egj.pokemon_species_id = p.pokemon_species_id
        order by egj.id
        limit 1
    ) as egg_group1,
    (
        select en.it_name
        from pokemon_v2_pokemonegggroup egj
            join egg_group_names en on en.id = egj.egg_group_id
        where egj.pokemon_species_id = p.pokemon_species_id
        order by egj.id
        limit 1
        offset 1
    ) as egg_group2
from pokemon_v2_pokemon p
    join (select * from pkmn_type where slot = 1) t1 on t1.pokemon_id = p.id
    left join (select * from pkmn_type where slot = 2) t2 on t2.pokemon_id = p.id
    join (select * from pkmn_names) pn on pn.id = p.pokemon_species_id
    join pokemon_v2_pokemonegggroup egj on egj.pokemon_species_id = p.pokemon_species_id
    join (select * from egg_group_names) en on en.id = egj.egg_group_id;

drop view if exists move;
create view move as
select
    m.*,
    mn.name as it_name,
    t.it_name as type_it_name
from pokemon_v2_move m
    join pokemon_v2_movename mn on mn.move_id = m.id
    join type t on t.id = m.type_id
where
    mn.language_id = (
        select id
        from pokemon_v2_language
        where iso3166 = 'it'
        limit 1
    );

drop view if exists learnset;
create view learnset as
select
    j.id as join_id,

    p.id as pkmn_id,
    p.name as pkmn_name,

    m.id as move_id,
    m.name as move_name,

    ml.id as learning_method_id,
    ml.name as learning_method_name,

    vg.id as game_id,
    vg.name as game_name
from pokemon_v2_pokemonmove j
    join pokemon_v2_movelearnmethod ml on j.move_learn_method_id = ml.id
    join pokemon_v2_versiongroup vg on j.version_group_id = vg.id
    join pokemon_v2_pokemon p on j.pokemon_id = p.id
    join pokemon_v2_move m on j.move_id = m.id;
