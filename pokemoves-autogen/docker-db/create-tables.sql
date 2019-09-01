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
    identifier character(27),
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
    identifier character(23),
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
    identifier character(17)
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
    identifier character(5),
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
