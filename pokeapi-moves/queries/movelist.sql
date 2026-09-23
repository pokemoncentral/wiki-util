select
    p.id,
    p.name,
    p.type1,
    p.type2,
    l.learning_method_name,
    l.game_name,
    (
        case l.learning_method_name
            when 'level-up' then json_group_array(j.level)
            else '[]'
        end
    ) as levels
from learnset l
    join pkmn p on l.pkmn_id = p.id
    join (
        select id, level
        from pokemon_v2_pokemonmove
    ) j on j.id = l.join_id
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
