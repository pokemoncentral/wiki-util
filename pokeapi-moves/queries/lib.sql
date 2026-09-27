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
        j.pokemon_id,
        j.slot,
        t.it_name
    from pokemon_v2_pokemontype j
        join type t on t.id = j.type_id
),
pkmn_species as (
    select
        ps.id,
        pn.name,
        ps.is_baby
    from pokemon_v2_pokemonspecies ps
        join pokemon_v2_pokemonspeciesname pn on pn.pokemon_species_id = ps.id
    where
        pn.language_id = (
            select id
            from pokemon_v2_language
            where iso3166 = 'it'
            limit 1
        )
),
pkmn_egg_group as (
    select
        egj.pokemon_species_id as species_id,
        en.name as it_name
    from pokemon_v2_pokemonegggroup egj
        join pokemon_v2_egggroupname en on en.egg_group_id = egj.egg_group_id
    where
        en.language_id = (
            select id
            from pokemon_v2_language
            where iso3166 = 'it'
            limit 1
        )
    order by en.name
),
pkmn_form as (
    select
        f.pokemon_id,
        f.form_order,
        fn.name as it_name
    from pokemon_v2_pokemonform f
        join pokemon_v2_pokemonformname fn on fn.pokemon_form_id = f.id
        join pokemon_v2_pokemon p on p.id = f.pokemon_id
    where
        fn.language_id = (
            select id
            from pokemon_v2_language
            where iso3166 = 'it'
            limit 1
        )
        and p.pokemon_species_id in (
            select pokemon_species_id
            from pokemon_v2_pokemon
            group by pokemon_species_id
            having count(*) > 1
        )
)
select
    p.id,
    p.pokemon_species_id as species_id,
    ps.name,
    f.it_name as form_name,
    f.form_order,
    ps.is_baby,
    t1.it_name as type1,
    t2.it_name as type2,
    (
        select it_name
        from pkmn_egg_group
        where species_id = p.pokemon_species_id
        limit 1
    ) as egg_group1,
    (
        select it_name
        from pkmn_egg_group
        where species_id = p.pokemon_species_id
        limit 1
        offset 1
    ) as egg_group2
from pokemon_v2_pokemon p
    join pkmn_species ps on ps.id = p.pokemon_species_id
    join (select * from pkmn_type where slot = 1) t1 on t1.pokemon_id = p.id
    left join (select * from pkmn_type where slot = 2) t2 on t2.pokemon_id = p.id
    left join pkmn_form f on f.pokemon_id = p.id;

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

-- drop table if exists evolution_chain_forwards;
create table if not exists evolution_chain_forwards (
    id integer primary key,
    species_id integer,
    chain_id integer,
    chain jsonb,
    types jsonb
);
insert into evolution_chain_forwards(species_id, chain_id, chain, types)
with evo_forwards(species_id, chain_id, evolves_from, chain, types) as (
    select
        final_stage.id as species_id,
        final_stage.evolution_chain_id as chain_id,
        final_stage.evolves_from_species_id as evolves_from,
        jsonb_array(final_stage.id) as chain,
        case
            when p.type2 is null then jsonb_array(p.type1)
            else jsonb_array(p.type1, p.type2)
        end as type
    from pokemon_v2_pokemonspecies final_stage
        join pkmn p on p.species_id = final_stage.id
    where
        final_stage.id not in (
            select evolves_from_species_id
            from pokemon_v2_pokemonspecies
            where evolves_from_species_id is not null
        )
        -- This is a hack to prevent this insert statement from running if
        -- there is already data in the table it populates.
        -- It needs to be here, in the base case of the recursive CTE, to stop
        -- the recursive CTE from executing in the first place, which is the
        -- slow part we want to avoid.
        and not exists (select 1 from evolution_chain_forwards)
    union
    select
        pre_evo.id as species_id,
        pre_evo.evolution_chain_id as chain_id,
        pre_evo.evolves_from_species_id as evolves_from,
        jsonb_array_insert(evo.chain, '$[0]', pre_evo.id) as chain,
        case
            when p.type2 is null then jsonb_array_insert(evo.types, '$[0]', p.type1)
            else jsonb_array_insert(evo.types, '$[0]', p.type1, '$[1]', p.type2)
        end as types
    from evo_forwards evo
        join pokemon_v2_pokemonspecies pre_evo on pre_evo.id = evo.evolves_from
        join pkmn p on p.species_id = pre_evo.id
)
select
    species_id,
    chain_id,
    jsonb_group_array(chain) as chain,
    jsonb_group_array(types) as types
from evo_forwards
group by species_id;

drop view if exists learnset;
create view learnset as
select
    j.id as join_id,
    p.id as pkmn_id,
    p.name as pkmn_name,
    m.id as move_id,
    m.name as move_name,
    ml.name as learning_method_name,
    vg.name as game_name
from pokemon_v2_pokemonmove j
    join pokemon_v2_movelearnmethod ml on j.move_learn_method_id = ml.id
    join pokemon_v2_versiongroup vg on j.version_group_id = vg.id
    join pokemon_v2_pokemon p on j.pokemon_id = p.id
    join pokemon_v2_move m on j.move_id = m.id;
