set :root, :C4
set :root_angle, -1
set :fifths_angle, -1
set :thirds_angle, -1
set :fourths_angle, -1
set :sevenths_angle, -1
set :ninth_angle, -1
set :bninth_angle, -1
set :sninth_angle, -1

live_loop :chord do
  root = get[:root]
  (play [(root if get[:root_angle] >= 0),
         (root + 7 if get[:fifths_angle] >= 0),
         (root + 4  if get[:thirds_angle] < 5 and get[:thirds_angle] > 2),
         (root + 3 if get[:thirds_angle] >= 0 and (get[:thirds_angle] > 5 or get[:thirds_angle] < 2)),
         (root + 11 if get[:sevenths_angle] < 5 and get[:sevenths_angle] > 2),
         (root + 10 if get[:sevenths_angle] >= 0 and (get[:sevenths_angle] > 5 or get[:sevenths_angle] < 2)),
         (root + 5 if get[:fourths_angle] >= 0),
         (root + 14 if get[:ninth_angle] >= 0),
         (root + 15 if get[:sninth_angle] >= 0),
         (root + 13 if get[:bninth_angle] >= 0)], amp: 10)
  sleep 1
end

live_loop :tower do
  use_real_time
  id, x, y, angle = sync "/osc/tuio/fiducial"
  set :root, :C4 if id == 44 and angle > -1
  set :root, :F4 if id == 45 and angle > -1
  set :root, :A4 if id == 46 and angle > -1
  set :root, :G4 if id == 47 and angle > -1
  set :root_angle, angle if (id == 44 and get[:root] == :C4) or (id == 45 and get[:root] == :F4) or(id == 46 and get[:root] == :A4) or (id == 47 and get[:root] == :G4)
  set :fifths_angle, angle if id == 0
  set :thirds_angle, angle if id == 1
  set :fourths_angle, angle if id == 3
  set :sevenths_angle, angle if id == 2
  set :ninth_angle, angle if id == 4
  set :sninth_angle, angle if id == 5
  set :bninth_angle, angle if id == 6
end

live_loop :button do
  use_real_time
  key, _ = sync "/osc/key"
end
