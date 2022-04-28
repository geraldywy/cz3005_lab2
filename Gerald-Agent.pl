:-dynamic([
  %% Track cells
  visited/2,
  wumpus/2,
  confundus/2,
  tingle/2,
  glitter/2,
  stench/2,
  wall/2,
  current/3,
  safe/2,
  wumpusXY/2, %% exact wumpus cell

  %% Track game state
  wumpusdeath/0, %% flag to see if wumpus has been killed
  nowumpus/2,
  noportal/2,
  stenchcnt/1, %% tracks number of stench cells visited
  hasarrow/0,
  wumpus_found_flag/0, %% flag to see if wumpus has been located

  maxmoves/1, %% limit number of moves before giving up
  %% misc tracks - flags to indicate special states
  back2origin/0, %% give up flag
  gamble/0 %% gamble flag
]).

resetmemory:-
  retractall(visited(_,_)),
  retractall(wumpus(_,_)),
  retractall(confundus(_,_)),
  retractall(tingle(_,_)),
  retractall(glitter(_,_)),
  retractall(stench(_,_)),
  retractall(wall(_,_)),
  retractall(stenchcnt(_)),
  retractall(wumpusXY(_,_)),
  retractall(noportal(_,_)),
  retractall(nowumpus(_,_)),
  retractall(current(_,_,_)),
  retractall(safe(_,_)),
  retractall(maxmoves(_)),
  retractall(back2origin),
  retractall(gamble),
  retractall(wumpus_found_flag),
  assert(current(0,0,rnorth)),
  assert(safe(0,0)),
  assert(visited(0,0)),
  assert(stenchcnt(0)),
  assert(maxmoves(500))
  .

reborn:-
  resetmemory,
  retractall(wumpusdeath),
  assert(hasarrow).

reposition(L):-
  resetmemory,
  [_, Stnch, Tngl, Gltr, _, _] = L,
  mark_stench(Stnch), handle_tingle(Tngl), handle_glitter(Gltr).

%% change agent behaviour as the game drags out
movecounter:-
  maxmoves(N), A is N-1,
  (
    (A == 0, assert(back2origin)); (A == 100, assert(gamble)); true
  ),
  retract(maxmoves(N)), assert(maxmoves(A)).

%% simple loop function to clear lanes with arrows
loop(M,N,BaseX,BaseY,Xoffset,Yoffset):-
  between(M, N, I),
  NewX is BaseX + (I * Xoffset),
  NewY is BaseY + (I * Yoffset),
  retract_wumpus(NewX,NewY),
  I >= N, !.
  loop(M,I,BaseX,BaseY,Xoffset,Yoffset).

move(A,L):-
  [Cnfd, Stnch, Tngl, Gltr, Bump, Scream] = L,
  (
    current(X, Y, D),
    (A == moveforward -> (
      Bump == on -> (
        ((D == rnorth, NewY is Y+1, mark_wall(X,NewY), false) ;
        (D == reast, NewX is X+1, mark_wall(NewX,Y), false) ;
        (D == rsouth, NewY is Y-1, mark_wall(X,NewY), false) ;
        (D == rwest, NewX is X-1, mark_wall(NewX,Y)))
      ) ; Cnfd == on -> reposition(L); do_forward, movecounter, mark_stench(Stnch), handle_tingle(Tngl), handle_glitter(Gltr)
    ),
    retract_portal(X,Y), retract_wumpus(X,Y), !);
    (A == shoot -> retractall(hasarrow), (Scream == on -> (
      assert(wumpusdeath),
      (
        wumpusXY(X,Y),
        (retractall(wumpus(_,_)); true),
        (retractall(wumpusXY(_,_)); true),
        (retractall(stench(_,_)); true),
        assert(safe(X,Y))
      )
    ); (
      (
        (D == rnorth, loop(1, 20, X, Y, 0, 1));
        (D == rsouth, loop(1, 20, X, Y, 0, -1));
        (D == reast, loop(1, 20, X, Y, 1, 0));
        (D == rwest, loop(1, 20, X, Y, -1, 0))
      )
    )), !);
    (A == turnleft -> turn(turnleft), !);
    (A == turnright -> turn(turnright), !);
    (A == pickup -> retract(glitter(X,Y)), !)
  ).

turn(Dir):-
  current(X,Y,D),
  (
    (Dir == turnright,
      (
        (D == rnorth, retract(current(X,Y,D)), assert(current(X,Y,reast)), !);
        (D == reast, retract(current(X,Y,D)), assert(current(X,Y,rsouth)), !);
        (D == rsouth, retract(current(X,Y,D)), assert(current(X,Y,rwest)), !);
        (D == rwest, retract(current(X,Y,D)), assert(current(X,Y,rnorth)))
      ));
    (Dir == turnleft,
      (
        (D == rnorth, retract(current(X,Y,D)), assert(current(X,Y,rwest)), !);
        (D == reast, retract(current(X,Y,D)), assert(current(X,Y,rnorth)), !);
        (D == rsouth, retract(current(X,Y,D)), assert(current(X,Y,reast)), !);
            (D == rwest, retract(current(X,Y,D)), assert(current(X,Y,rsouth)))
      ))
  ).

do_forward:-
  current(X,Y,D),
  (
    (D == rnorth, NewY is Y+1, retract(current(X,Y,D)), assert((current(X,NewY,D))), assert(visited(X,NewY)), !);
    (D == reast, NewX is X+1, retract(current(X,Y,D)), assert((current(NewX,Y,D))), assert(visited(NewX,Y)), !);
    (D == rsouth, NewY is Y-1, retract(current(X,Y,D)), assert((current(X,NewY,D))), assert(visited(X,NewY)), !);
    (D == rwest, NewX is X-1, retract(current(X,Y,D)), assert((current(NewX,Y,D))), assert(visited(NewX,Y)))
  ).

%% walls cannot be npcs
mark_wall(X,Y):-
  (
    \+wall(X,Y), assert(wall(X,Y)),
    (
      (confundus(X,Y), wumpus(X,Y), retract(confundus(X,Y)), retract(wall(X,Y)));
      (confundus(X,Y), retract(confundus(X,Y)));
      (wumpus(X,Y), retract(wumpus(X,Y)));
      true
    ),
    (
      (\+nowumpus(X,Y), \+noportal(X,Y), assert(nowumpus(X,Y)), assert(noportal(X,Y)));
      (\+nowumpus(X,Y), assert(nowumpus(X,Y)));
      (\+noportal(X,Y), assert(noportal(X,Y)));
      true
    )
  );
  true.

retract_wumpus(X,Y):-
  (
    (wumpus(X,Y), retract(wumpus(X,Y))); true
  ),
  (
    (\+nowumpus(X,Y), assert(nowumpus(X,Y))); true
  ),
  (
    (\+safe(X,Y), nowumpus(X,Y), noportal(X,Y), assert(safe(X,Y))); true
  ).

retract_portal(X,Y):-
  (
    (confundus(X,Y), retract(confundus(X,Y))); true
  ),
  (
    (\+noportal(X,Y), assert(noportal(X,Y))); true
  ),
  (
    (\+safe(X,Y), nowumpus(X,Y), noportal(X,Y), assert(safe(X,Y))); true
  ).

%% mark stench, find wumpus coord if possible
mark_stench(State):-
  current(X,Y,_),
  XL is X-1, XR is X+1, YU is Y+1, YD is Y-1,
  (State == on -> (
    (\+visited(XL,Y), \+wumpus(XL,Y), \+tingle(XL,Y), \+wall(XL,Y), \+nowumpus(XL,Y), \+wumpus_found_flag, \+wumpusdeath, assert(wumpus(XL,Y)), false) ;
    (\+visited(XR,Y), \+wumpus(XR,Y), \+tingle(XR,Y), \+wall(XR,Y), \+nowumpus(XR,Y), \+wumpus_found_flag, \+wumpusdeath, assert(wumpus(XR,Y)), false) ;
    (\+visited(X,YU), \+wumpus(X,YU), \+tingle(X,YU), \+wall(X,YU), \+nowumpus(X,YU), \+wumpus_found_flag, \+wumpusdeath, assert(wumpus(X,YU)), false) ;
    (\+visited(X,YD), \+wumpus(X,YD), \+tingle(X,YD), \+wall(X,YD), \+nowumpus(X,YD), \+wumpus_found_flag, \+wumpusdeath, assert(wumpus(X,YD)), false) ;
    ((\+stench(X,Y), assert(stench(X,Y)), stenchcnt(N), NewN is N+1, retract(stenchcnt(N)), assert(stenchcnt(NewN))), false) ;
    find_wumpus
  );
  (retract_wumpus(XL,Y), retract_wumpus(XR,Y), retract_wumpus(X,YU), retract_wumpus(X,YD))
  );
  true.

handle_glitter(State):-
  (State == on, current(X,Y,_), \+glitter(X,Y), assert(glitter(X,Y)));
  true.


handle_tingle(State):-
  current(X,Y,_),
  XL is X-1, XR is X+1, YU is Y+1, YD is Y-1,
  (State == on -> (
    ( \+visited(XL,Y), \+confundus(XL,Y), \+tingle(XL,Y), \+wall(XL,Y), \+noportal(XL,Y), assert(confundus(XL,Y)), false) ;
    ( \+visited(XR,Y), \+confundus(XR,Y), \+tingle(XR,Y), \+wall(XR,Y), \+noportal(XR,Y), assert(confundus(XR,Y)), false) ;
    ( \+visited(X,YU), \+confundus(X,YU), \+tingle(X,YU), \+wall(X,YU), \+noportal(X,YU), assert(confundus(X,YU)), false) ;
    ( \+visited(X,YD), \+confundus(X,YD), \+tingle(X,YD), \+wall(X,YD), \+noportal(X,YD), assert(confundus(X,YD)), false) ;
    (\+tingle(X,Y), assert(tingle(X,Y)); true)
  );
    (retract_portal(XL,Y), retract_portal(XR,Y), retract_portal(X,YU), retract_portal(X,YD))
  );
  true.

%% attempt to find and mark wumpus
find_wumpus:-
  findall([Xn,Yn], stench(Xn,Yn), Coords),
  \+wumpus_found_flag -> (
    (stenchcnt(2) -> check_zone_with_two(Coords); true),
    wumpus_found_flag -> (
      wumpusXY(X,Y),
      retractall(wumpus(_,_)),
      assert(wumpus(X,Y))
    ); true
  ); true
  .

%% attempt to triangulate wumpus position with 2 stench cells
%% this only holds true if there is not more than one wumpus
check_zone_with_two(Coords):-
  nth0(0, Coords, First),
  nth0(1, Coords, Second),
  nth0(0, First, Firstx),
  nth0(0, Second, Secondx),
  nth0(1, First, Firsty),
  nth0(1, Second, Secondy),
  (
    %% directly opposite cases
    (Firstx == Secondx, Xw is Firstx, Yw is (Firsty + Secondy) / 2, assert(wumpusXY(Xw,Yw)), assert(wumpus_found_flag), !);
    (Firsty == Secondy, Xw is (Firstx + Secondx) / 2, Yw is Firsty, assert(wumpusXY(Xw,Yw)), assert(wumpus_found_flag), !)
  ).

%% attempt to triangulate wumpus position with 3 stench cells
check_zone_with_three(Coords):-
  nth0(0, Coords, First),
  nth0(1, Coords, Second),
  nth0(2, Coords, Third),
  nth0(0, First, Firstx),
  nth0(0, Second, Secondx),
  nth0(0, Third, Thirdx),
  nth0(1, First, Firsty),
  nth0(1, Second, Secondy),
  nth0(1, Third, Thirdy),
  (
    (Firstx == Secondx, nth0(1, Third, Thirdy), Xw is Firstx, Yw is Thirdy, assert(wumpusXY(Xw,Yw)), assert(wumpus_found_flag), !);
    (Firstx == Thirdx, nth0(1, Second, Secondy), Xw is Firstx, Yw is Secondy, assert(wumpusXY(Xw,Yw)), assert(wumpus_found_flag), !);
    (Secondx == Thirdx, nth0(1, First, Firsty), Xw is Secondx, Yw is Firsty, assert(wumpusXY(Xw,Yw)), assert(wumpus_found_flag), !);
    (Firsty == Secondy, nth0(0, Third, Thirdx), Yw is Firsty, Xw is Thirdx, assert(wumpusXY(Xw,Yw)), assert(wumpus_found_flag), !);
    (Firsty == Thirdy, nth0(0, Second, Secondx), Yw is Firsty, Xw is Secondx, assert(wumpusXY(Xw,Yw)), assert(wumpus_found_flag), !);
    (Secondy == Thirdy, nth0(0, First, Firstx), Yw is Secondy, Xw is Firstx, assert(wumpusXY(Xw,Yw)), assert(wumpus_found_flag))
  ).


%% agent can decide to continue or give up
explore(L):-
  (current(Xcur,Ycur,Dcur), back2origin, Xcur == 0, Ycur == 0, Dcur == rnorth) -> false;
  (
    current(X,Y,_),
    (
      (glitter(X,Y), A = pickup);
      (back2origin, give_up(A));
      (stench(X,Y), danger(A));
      plan(A)
    ),
    L = [A]
  ).

give_up(L):-
  current(X,Y,D),
  XL is X-1, XR is X+1, YU is Y+1, YD is Y-1,
  (
    (XL == 0, Y == 0, insist_move_rwest(L));
    (X == 0, YD == 0, insist_move_rsouth(L));
    (XR == 0, Y == 0, insist_move_reast(L));
    (X == 0, YU == 0, insist_move_rnorth(L));
    (X == 0, Y == 0, insist_face_rnorth(L))
  );
  plan(L).

insist_face_rnorth(L):-
  L = turnleft.

/*
  insist on certain actions until it faces right orientation, keeps turning left otherwise
*/
insist_move_rwest(L):-
  current(_,_,D),
  D == rwest -> L = moveforward;
  L = turnleft.

insist_move_reast(L):-
  current(_,_,D),
  D == reast -> L = moveforward;
  L = turnleft.

insist_move_rsouth(L):-
  current(_,_,D),
  D == rsouth -> L = moveforward;
  L = turnleft.

insist_move_rnorth(L):-
  current(_,_,D),
  D == rnorth -> L = moveforward;
  L = turnleft.

insist_shoot_rwest(L):-
  current(_,_,D),
  D == rwest -> L = shoot;
  L = turnleft.

insist_shoot_reast(L):-
  current(_,_,D),
  D == reast -> L = shoot;
  L = turnleft.

insist_shoot_rsouth(L):-
  current(_,_,D),
  D == rsouth -> L = shoot;
  L = turnleft.

insist_shoot_rnorth(L):-
  current(_,_,D),
  D == rnorth -> L = shoot;
  L = turnleft.


plan(L):-
  current(X,Y,_),
  XL is X-1, XR is X+1, YU is Y+1, YD is Y-1,
  (
    (\+visited(XL,Y), \+wall(XL,Y), \+wumpus(XL,Y), \+confundus(XL,Y), insist_move_rwest(L));
    (\+visited(X,YD), \+wall(X,YD), \+wumpus(X,YD), \+confundus(X,YD), insist_move_rsouth(L));
    (\+visited(XR,Y), \+wall(XR,Y), \+wumpus(XR,Y), \+confundus(XR,Y), insist_move_reast(L));
    (\+visited(X,YU), \+wall(X,YU), \+wumpus(X,YU), \+confundus(X,YU), insist_move_rnorth(L))
  );
  (
    checkvisited(NewD),
    (
      (NewD == rwest, insist_move_rwest(L));
      (NewD == reast, insist_move_reast(L));
      (NewD == rnorth, insist_move_rnorth(L));
      (NewD == rsouth, insist_move_rsouth(L))
    )
  ).


/*
  Below contains optimizations for agent behaviour.
*/

%% an alternative version that tries for full completion if desperate enough
%% although this could potentially result in an infinite loop
%% and since we are not allowed to have a god agent keeping track of "portal failures"
%% we do not know exactly how many times we have tried gambling with a portal
%% so this is not used but left here as reference.
plan_with_bias_for_completion(L):-
  current(X,Y,_),
  XL is X-1, XR is X+1, YU is Y+1, YD is Y-1,
  (
    (\+visited(XL,Y), \+wall(XL,Y), \+wumpus(XL,Y), (gamble ; \+confundus(XL,Y)), insist_move_rwest(L));
    (\+visited(X,YD), \+wall(X,YD), \+wumpus(X,YD), (gamble ; \+confundus(X,YD)), insist_move_rsouth(L));
    (\+visited(XR,Y), \+wall(XR,Y), \+wumpus(XR,Y), (gamble ; \+confundus(XR,Y)), insist_move_reast(L));
    (\+visited(X,YU), \+wall(X,YU), \+wumpus(X,YU), (gamble ; \+confundus(X,YU)), insist_move_rnorth(L))
  );
  (
    checkvisited(NewD),
    (
        (NewD == rwest, insist_move_rwest(L));
        (NewD == reast, insist_move_reast(L));
        (NewD == rnorth, insist_move_rnorth(L));
        (NewD == rsouth, insist_move_rsouth(L))
    )
  ).

danger(L):-
  current(X,Y,_),
  XL is X-1, XR is X+1, YU is Y+1, YD is Y-1,
  (
    wumpus_found_flag, hasarrow,
    (wumpusXY(XL,Y), insist_shoot_rwest(L));
    (wumpusXY(XR,Y), insist_shoot_reast(L));
    (wumpusXY(X,YU), insist_shoot_rnorth(L));
    (wumpusXY(X,YD), insist_shoot_rsouth(L))
  );
  (
    gamble, hasarrow, random_shoot(L)
  );
  plan(L).

random_shoot(L):-
  current(X,Y,_),
  XL is X-1, XR is X+1, YU is Y+1, YD is Y-1,
  (
    (wumpus(XL,Y), \+wall(XL,YU), \+wall(XL,YD), insist_shoot_rwest(L));
    (wumpus(XR,Y), \+wall(XR,YU), \+wall(XR,YD), insist_shoot_reast(L));
    (wumpus(X,YU), \+wall(XR,YU), \+wall(XL,YU), insist_shoot_rnorth(L));
    (wumpus(X,YD), \+wall(XR,YD), \+wall(XL,YD), insist_shoot_rnorth(L))
  );
  (
    (wumpus(XL,Y), insist_shoot_rwest(L));
    (wumpus(XR,Y), insist_shoot_reast(L));
    (wumpus(X,YU), insist_shoot_rnorth(L));
    (wumpus(X,YD), insist_shoot_rsouth(L))
  ).

%% attempt to visit least visited cell
checkvisited(NewD):-
  current(X,Y,_),
  XL is X-1, XR is X+1, YU is Y+1, YD is Y-1,
  (
    ((wall(XL,Y); confundus(XL,Y); wumpus(XL,Y)), Rwestcount = 999999);
    aggregate_all(count, visited(XL,Y), Rwestcount)
  ),
  (
    ((wall(XR,Y); confundus(XR,Y); wumpus(XR,Y)), Reastcount = 999999);
    aggregate_all(count, visited(XR,Y), Reastcount)
  ),
  (
    ((wall(X,YU); confundus(X,YU); wumpus(X,YU)), Rnorthcount = 999999);
    aggregate_all(count, visited(X,YU), Rnorthcount)
  ),
  (
    ((wall(X,YD); confundus(X,YD); wumpus(X,YD)), Rsouthcount = 999999);
    aggregate_all(count, visited(X,YD), Rsouthcount)
  ),
  sort([Rwestcount, Reastcount, Rnorthcount, Rsouthcount], List),
  nth0(0, List, Smallest),
  (
    (Smallest == Rwestcount, NewD = rwest);
    (Smallest == Reastcount, NewD = reast);
    (Smallest == Rnorthcount, NewD = rnorth);
    (Smallest == Rsouthcount, NewD = rsouth)
  ).