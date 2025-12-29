SET statement_timeout = 0;
SET lock_timeout = 0;
SET idle_in_transaction_session_timeout = 0;
SET client_encoding = 'UTF8';
SET standard_conforming_strings = on;
SELECT pg_catalog.set_config('search_path', '', false);
SET check_function_bodies = false;
SET xmloption = content;
SET client_min_messages = warning;
SET row_security = off;
SET default_tablespace = '';
SET default_with_oids = false;

set search_path = public;

create table lpza_move_types (
    id integer not null primary key,
    "name" text not null
);
insert into lpza_move_types values
(0, 'normale'),
(1, 'lotta'),
(2, 'volante'),
(3, 'veleno'),
(4, 'terra'),
(5, 'roccia'),
(6, 'coleottero'),
(7, 'spettro'),
(8, 'acciaio'),
(9, 'fuoco'),
(10, 'acqua'),
(11, 'erba'),
(12, 'elettro'),
(13, 'psico'),
(14, 'ghiaccio'),
(15, 'drago'),
(16, 'buio'),
(17, 'folletto');

ALTER TABLE lpza_move_types OWNER TO postgres;

create table lpza_move_categories (
    id integer not null primary key,
    "name" text not null
);
insert into lpza_move_categories values
(0, 'stato'),
(1, 'fisico'),
(2, 'speciale');

ALTER TABLE lpza_move_categories OWNER TO postgres;

CREATE TABLE lpza_moves (
    MoveID integer not null primary key,
    CanUseMove boolean not null,
    "Type" integer not null,
    Quality integer not null,
    Category integer not null,
    Power integer not null,
    Accuracy integer not null,
    PP integer not null,
    "Priority" integer not null,
    HitMax integer not null,
    HitMin integer not null,
    Inflict text not null,
    CritStage integer not null,
    Flinch integer not null,
    EffectSequence integer not null,
    Recoil integer not null,
    SelfHeal integer not null,
    DamageHeal integer not null,
    RawTarget integer not null,
    StatAmps text not null,
    "Affinity" text not null,
    FlagMakesContact boolean not null,
    FlagCharge boolean not null,
    FlagRecharge boolean not null,
    FlagProtect boolean not null,
    FlagReflectable boolean not null,
    FlagSnatch boolean not null,
    FlagMirror boolean not null,
    FlagPunch boolean not null,
    FlagSound boolean not null,
    FlagDance boolean not null,
    FlagGravity boolean not null,
    FlagDefrost boolean not null,
    FlagDistanceTriple boolean not null,
    FlagHeal boolean not null,
    FlagIgnoreSubstitute boolean not null,
    FlagFailSkyBattle boolean not null,
    FlagAnimateAlly boolean not null,
    FlagMetronome boolean not null,
    FlagFailEncore boolean not null,
    FlagFailMeFirst boolean not null,
    FlagFutureAttack boolean not null,
    FlagPressure boolean not null,
    FlagCombo boolean not null,
    FlagNoSleepTalk boolean not null,
    FlagNoAssist boolean not null,
    FlagFailCopycat boolean not null,
    FlagFailMimic boolean not null,
    FlagFailInstruct boolean not null,
    FlagPowder boolean not null,
    FlagBite boolean not null,
    FlagBullet boolean not null,
    FlagNoMultiHit boolean not null,
    FlagNoEffectiveness boolean not null,
    FlagSheerForce boolean not null,
    FlagSlicing boolean not null,
    FlagWind boolean not null,
    Unknown57 boolean not null,
    Unknown58 boolean not null,
    Unknown59 boolean not null,
    Unknown60 boolean not null,
    Unknown61 boolean not null,
    Unused62 boolean not null,
    Unused63 boolean not null,
    Unused64 boolean not null,
    Unused65 boolean not null,
    Unused66 boolean not null,
    Unused67 boolean not null,
    Unused68 boolean not null,
    Unused69 boolean not null,
    Unused70 boolean not null,
    Unused71 boolean not null,
    FlagCantUseTwice boolean not null
);


ALTER TABLE lpza_moves OWNER TO postgres;

ALTER TABLE ONLY lpza_moves
    ADD CONSTRAINT lpza_moves_type_fkey FOREIGN KEY ("Type") REFERENCES lpza_move_types(id),
    ADD CONSTRAINT lpza_moves_category_fkey FOREIGN KEY (Category) REFERENCES lpza_move_categories(id);

--
-- Name: lpza_move_params; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE lpza_move_params (
    WazaId integer not null,
    ChargeFrame integer not null,
    AttackLoopFrame integer not null,
    SpawnOrigin integer not null,
    SpawnLocator text,
    SpawnOffsetX real not null,
    SpawnOffsetY real not null,
    SpawnOffsetZ real not null,
    ShotDirection integer not null,
    CorrectTargetType integer not null,
    ImpactMotionSpeed real not null,
    PlayWazaMoveType integer not null,
    WazaRangeMin real not null,
    WazaRangeMax real not null,
    HeightTolerance integer not null,
    EffectiveRange real not null,
    MinShootNum integer not null,
    MaxShootNum integer not null,
    HitPer integer not null,
    WazaRecastTime integer not null,
    EffectTime real not null,
    EffectValue integer not null,
    AddMegaPowerValue real not null,
    PlayedMotionSpeed integer not null,
    OverwriteBulletId1 integer not null,
    ReplaceBulletId1 integer not null,
    OverwriteBulletId2 integer not null,
    ReplaceBulletId2 integer not null,
    OverwriteBulletId3 integer not null,
    ReplaceBulletId3 integer not null,
    OverwriteBulletId4 integer not null,
    ReplaceBulletId4 integer not null,
    OverwriteBulletId5 real not null,
    ReplaceBulletId5 real not null,
    BulletCorrectScale real not null
);

ALTER TABLE lpza_move_params OWNER TO postgres;

ALTER TABLE ONLY lpza_move_params
    ADD CONSTRAINT lpza_move_params_wazaid_fkey FOREIGN KEY (WazaId) REFERENCES lpza_moves(MoveID);

create table lpza_move_names (
    id integer not null primary key,
    "it_name" text not null
);
alter table lpza_move_names owner to postgres;

alter table only lpza_move_names
    add constraint lpza_move_names_id_fkey foreign key (id) references lpza_moves(MoveId);

create view lpza_move_lua as
select
    lpza_move_names.it_name as name,
    lpza_move_types.name as type,
    lpza_move_categories.name as category,
    case lpza_moves.power
        when 0 then null
        when 1 then null
        else lpza_moves.power
    end as power,
    lpza_move_params.wazarecasttime as recharge,
    json_object(
        'effective': lpza_move_params.effectiverange,
        'min': lpza_move_params.wazarangemin,
        'max': lpza_move_params.wazarangemax
    ) as "range",
    lpza_moves.moveid as move_id
from lpza_moves
    join lpza_move_names on lpza_moves.moveid = lpza_move_names.id
    join lpza_move_types on lpza_move_types.id = lpza_moves."Type"
    join lpza_move_categories on lpza_move_categories.id = lpza_moves.Category
    join lpza_move_params on lpza_moves.moveid = lpza_move_params.wazaid;

ALTER VIEW lpza_move_lua OWNER TO postgres;

create function to_lua_index(s text) returns text as $$
    select case
        when s similar to '[_a-zA-Z]+[_a-zA-Z0-9]*'
            then '.' || lower(s)
        else
            format('["%s"]', lower(s))
    end
$$ language sql;

/*
$ mkdir out
$ chmod o+w out

copy (
select format(
    'm%s = { name = "%s", type = "%s", category = "%s", power = %s, recharge = %s, range = %s }',
    to_lua_index(m.name),
    m.name,
    m.type,
    m.category,
    coalesce(m.power::text, 'nil'),
    m.recharge,
    round((m.range ->> 'effective')::real)
) as lua
from lpza_move_lua as m
order by move_id asc
) to '/out/lzpa-moves.lua';
*/
