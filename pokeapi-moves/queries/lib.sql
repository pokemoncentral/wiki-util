drop view learnset;
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

drop view pkmn;
create view pkmn as
with type as (
    select
        j.id,
        j.type_id,
        j.pokemon_id,
        j.slot,
        t.name as name,
        tn.name as it_name
    from pokemon_v2_pokemontype j
        join pokemon_v2_type t on t.id = j.type_id
        join pokemon_v2_typename tn on tn.type_id = t.id
    where
        tn.language_id = (
            select id
            from pokemon_v2_language
            where iso3166 = 'it'
            limit 1
        )
)
select
    p.id as id,
    p.name as name,
    t1.it_name as type1,
    t2.it_name as type2
from pokemon_v2_pokemon p
    join (select * from type where slot = 1) t1 on t1.pokemon_id = p.id
    left join (select * from type where slot = 2) t2 on t2.pokemon_id = p.id;
