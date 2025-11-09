--
-- PostgreSQL database dump
--

-- Dumped from database version 11.5 (Debian 11.5-1.pgdg90+1)
-- Dumped by pg_dump version 11.5 (Debian 11.5-1.pgdg90+1)

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

--
-- Name: moves; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.moves (
    id integer NOT NULL,
    identifier text,
    generation_id integer,
    type_id integer,
    power integer,
    pp integer,
    accuracy integer,
    priority integer,
    target_id integer,
    damage_class_id integer,
    effect_id integer,
    effect_chance integer,
    contest_type_id integer,
    contest_effect_id integer,
    super_contest_effect_id integer
);


ALTER TABLE public.moves OWNER TO postgres;

--
-- Name: pokemon; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pokemon (
    id integer NOT NULL,
    identifier text,
    species_id integer,
    height integer,
    weight integer,
    base_experience integer,
    sortring integer,
    is_default boolean
);


ALTER TABLE public.pokemon OWNER TO postgres;

--
-- Name: pokemon_move_methods; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pokemon_move_methods (
    id integer NOT NULL,
    identifier text
);


ALTER TABLE public.pokemon_move_methods OWNER TO postgres;

--
-- Name: pokemon_moves; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.pokemon_moves (
    pokemon_id integer,
    version_group_id integer,
    move_id integer,
    pokemon_move_method_id integer,
    level integer,
    sorting integer
);


ALTER TABLE public.pokemon_moves OWNER TO postgres;

--
-- Name: version_groups; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.version_groups (
    id integer NOT NULL,
    identifier text,
    generation_id integer,
    sorting integer
);


ALTER TABLE public.version_groups OWNER TO postgres;

--
-- Name: moves moves_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.moves
    ADD CONSTRAINT moves_pkey PRIMARY KEY (id);


--
-- Name: pokemon_move_methods pokemon_move_methods_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pokemon_move_methods
    ADD CONSTRAINT pokemon_move_methods_pkey PRIMARY KEY (id);


--
-- Name: pokemon pokemon_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pokemon
    ADD CONSTRAINT pokemon_pkey PRIMARY KEY (id);


--
-- Name: version_groups version_groups_pkey; Type: CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.version_groups
    ADD CONSTRAINT version_groups_pkey PRIMARY KEY (id);


--
-- Name: pokemon_moves pokemon_moves_move_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pokemon_moves
    ADD CONSTRAINT pokemon_moves_move_id_fkey FOREIGN KEY (move_id) REFERENCES public.moves(id);


--
-- Name: pokemon_moves pokemon_moves_pokemon_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pokemon_moves
    ADD CONSTRAINT pokemon_moves_pokemon_id_fkey FOREIGN KEY (pokemon_id) REFERENCES public.pokemon(id);


--
-- Name: pokemon_moves pokemon_moves_pokemon_move_method_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pokemon_moves
    ADD CONSTRAINT pokemon_moves_pokemon_move_method_id_fkey FOREIGN KEY (pokemon_move_method_id) REFERENCES public.pokemon_move_methods(id);


--
-- Name: pokemon_moves pokemon_moves_version_group_id_fkey; Type: FK CONSTRAINT; Schema: public; Owner: postgres
--

ALTER TABLE ONLY public.pokemon_moves
    ADD CONSTRAINT pokemon_moves_version_group_id_fkey FOREIGN KEY (version_group_id) REFERENCES public.version_groups(id);

--
-- PostgreSQL database dump complete
--

--
-- Name: lpza_types; Type: TABLE; Schema: public; Owner: postgres
--

create table public.lpza_types (
    id integer not null primary key,
    "name" text not null
);
insert into public.lpza_types values
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

ALTER TABLE public.lpza_types OWNER TO postgres;

create table public.lpza_categories (
    id integer not null primary key,
    "name" text not null
);
insert into public.lpza_categories values
(0, 'stato'),
(1, 'fisico'),
(2, 'speciale');

ALTER TABLE public.lpza_categories OWNER TO postgres;

--
-- Name: moves_lpza; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.moves_lpza (
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


ALTER TABLE public.moves_lpza OWNER TO postgres;

ALTER TABLE ONLY public.moves_lpza
    ADD CONSTRAINT moves_lpza_type_fkey FOREIGN KEY ("Type") REFERENCES public.lpza_types(id),
    ADD CONSTRAINT moves_lpza_category_fkey FOREIGN KEY (Category) REFERENCES public.lpza_categories(id);

--
-- Name: moves_params_lpza; Type: TABLE; Schema: public; Owner: postgres
--

CREATE TABLE public.moves_params_lpza (
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

ALTER TABLE public.moves_params_lpza OWNER TO postgres;

ALTER TABLE ONLY public.moves_params_lpza
    ADD CONSTRAINT moves_params_lpza_wazaid_fkey FOREIGN KEY (WazaId) REFERENCES public.moves_lpza(MoveID);

create view public.moves_lpza_useful as
select
    public.moves.identifier as name,
    public.lpza_types.name as type,
    public.lpza_categories.name as category,
    public.moves.power as power,
    public.moves_params_lpza.wazarecasttime as recharge,
    json_object(
        'effective': public.moves_params_lpza.effectiverange,
        'min': public.moves_params_lpza.wazarangemin,
        'max': public.moves_params_lpza.wazarangemax
    ) as "range",
    public.moves.id as move_id
from public.moves
    join public.moves_lpza on public.moves_lpza.moveid = public.moves.id
    join public.lpza_types on public.lpza_types.id = public.moves_lpza."Type"
    join public.lpza_categories on public.lpza_categories.id = public.moves_lpza.Category
    join public.moves_params_lpza on public.moves_lpza.moveid = public.moves_params_lpza.wazaid;

ALTER VIEW public.moves_lpza_useful OWNER TO postgres;

/*
select format(
    'm%s = { name = "%s", type = "%s", category = "%s", power = %s, recharge = %s, range = %s }',
    case
        when m.name similar to '[_a-zA-Z]+[_a-zA-Z0-9]*'
            then '.' || lower(m.name)
        else
            format('["%s"]', lower(m.name))
    end,
    m.name,
    m.type,
    m.category,
    coalesce(m.power::text, 'nil'),
    m.recharge,
    round((m.range ->> 'effective')::real)
) as lua
from moves_lpza_useful as m
order by move_id asc
*/
