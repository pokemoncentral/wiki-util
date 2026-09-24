with items as (
    select i.id, itn.name as it_name
    from pokemon_v2_item i
        join pokemon_v2_itemname itn on itn.item_id = i.id
    where
        itn.language_id = (
            select id
            from pokemon_v2_language
            where iso3166 = 'it'
            limit 1
        )
),
join_table as (
    select
        j.id,
        j.level,
        mc.it_name as machine_name
    from pokemon_v2_pokemonmove j
        left join (
            select *
            from pokemon_v2_machine mc
                join items i on mc.item_id = i.id
        ) mc on j.move_id = mc.move_id
            and j.version_group_id = mc.version_group_id
)
select
    p.id,
    p.name,
    p.type1,
    p.type2,
    p.egg_group1,
    p.egg_group2,
    l.learning_method_name,
    l.game_name,
    (
        case l.learning_method_name
            when 'level-up' then json_group_array(j.level)
            else '[]'
        end
    ) as levels,
    (
        case l.learning_method_name
            when 'machine' then j.machine_name
            else null
        end
    ) as machine
from learnset l
    join pkmn p on l.pkmn_id = p.id
    join join_table j on j.id = l.join_id
where
    (:move is null or l.move_name = :move)
    and (:learning_method is null or l.learning_method_name = :learning_method)
    and (:game is null or l.game_name = :game)
group by
    l.learning_method_name,
    l.game_name,
    p.id
order by
    l.learning_method_name asc,
    l.game_name asc,
    p.id asc,
    j.level asc
