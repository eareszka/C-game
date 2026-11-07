# Movement task: Qiqirn (17) -- never off screen (and check every enemy)

From the user (2026-11-06), via the animation session, on Qiqirn: "should never go off screen".
- Qiqirn runs a border inset only L/R 50, T 45, B 50 px from the arena walls, but its new sheet
  (assets/enemies/redraws/17_qiqirn*.png, 52x52 frame drawn 2x = 104x104 on screen, art roughly 40x45 of
  that -> ~80x90 px) hangs off the edges, the top under the HUD. Inset the border by the DRAWN sprite's
  half-extent (+ a few px) so the whole body always stays inside the arena, in every direction view (its
  front/back/side frames differ in width). The art's opaque bounds per view can be read from the sheet.
- Then the same check for EVERY enemy: with the animation run many sheets got bigger (four views, 44-56 px
  frames). Any enemy whose movement clamps (x/y limits, border paths, wall slams, hover points) let its drawn
  sprite leave the arena or slide under the HUD should clamp by its sprite's real half-size. List what you
  changed. Bosses that are colossal by design (Physeter, Dajna, Olgoi-Khorkhoi...) are exempt where their
  size makes it impossible -- say which.
