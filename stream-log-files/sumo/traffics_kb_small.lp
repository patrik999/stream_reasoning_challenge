% Static KB


% Road structure of nodes and (taken from road newtwork)
node(i1).
node(i1b).
node(i2).
node(i2b).
node(i3).
node(i3b).
node(i4).
node(i4b).
node(i5).
node(i5b).
node(gneJ1).
node(gneJ13).
node(lnk1a).
node(lnk1b).
node(lnk1c).
node(o1).
node(o1b).
node(o2).
node(o2b).
node(o3).
node(o3b).
node(o4).
node(o4b).
node(o5).
node(o5b).

link(i1,i1b,we).
link(i1b,gneJ1,we).
link(i2,i2b,we).
link(i2b,gneJ1,we).
link(gneJ1,lnk1a,we).
link(lnk1a,lnk1b,we).
link(gneJ1,o1b,ew).
link(o1b,o1,ew).
link(lnk1b,lnk1a,ew).
link(lnk1a,gneJ1,ew).
link(lnk1b,lnk1c,we).
link(lnk1c,gneJ13,we).
link(gneJ13,o5b,we).
link(o5b,o5,we).
link(gneJ13,o4b,we).
link(o4b,o4,we).
link(gneJ13,lnk1c,ew).
link(lnk1c,lnk1b,ew).
link(i4,i4b,ew).
link(i4b,gneJ13,ew).
link(i3,i3b,ew).
link(i3b,gneJ13,ew).
link(i5,i5b,ew).
link(i5b,gneJ13,ew).
link(gneJ13,o5b,ew).
link(o2b,o2,ew).
link(gneJ1,o2b,ew).
link(o3b,o3,we).
link(gneJ13,o3b,we).
link(o4b,o4,we).
link(gneJ13,o4b,we).

maxSpeed(lnk1a,lnk1b,13). % max speed is in m/s (times 3.6 to km/h)
maxSpeed(lnk1b,lnk1c,13).
maxSpeed(lnk1c,lnk1b,13).
maxSpeed(lnk1b,lnk1a,13).

maxSpeed(X,Y,12) :- link(X,Y,D), not maxSpeed(X,Y,S).


% Traffic distribution on intersection
link_ratio(gneJ1, lnk1a, we, 100). % Ratio 100/100
link_ratio(gneJ1, o1b, ew, 100). % Ratio 100/100
link_ratio(gneJ13, o4b, we, 50). % Ratio 50/100
link_ratio(gneJ13, o5b, we, 50). % Ratio 50/100
link_ratio(gneJ13, lnk1c, ew, 75). % Ratio 75/100
link_ratio(gneJ13, o5b, ew, 25). % Ratio 25/100

% Traffic light red phases, first argument is incoming node, second is intersection node

% This signals are not allowed to be green at the same time
conflict_tl(gneJ1, i2b, i1b).
conflict_tl(gneJ1, i2b, lnk1a).
conflict_tl(gneJ13, i3b, i4b).
conflict_tl(gneJ13, i3b, lnk1c).
conflict_tl(gneJ13, i5b, i4b).
conflict_tl(gneJ13, i5b, lnk1c).
% Inverse
conflict_tl(X,Y,Z) :- conflict_tl(X,Z,Y).

% Vehicles types
vehType(carA) . % VW
vehType(carB) . % Fiat
vehType(carC) . % Bus
vehType(carD) . % BMW
vehType(carE) . % Mercedes

% Vehicle classification
isSubType(carA,familyCar) .
isSubType(carB,familyCar) .
isSubType(carC,truck) .
isSubType(carD,sportsCar) .
isSubType(carE,sportsCar) .
isSubType(familyCar,persVehicle) .
isSubType(sportsCar,persVehicle) .
isSubType(bus,utilVehicle) .
