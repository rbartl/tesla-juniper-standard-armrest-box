"""
TeslaBox v4 – Einhänge-Einsatz, Model Y Juniper Standard

Achsen: X = vorne(Kartenseite)->hinten, Y = links/rechts (Kragenseiten).

- Kragen NUR seitlich (±Y, beide Seiten), NICHT vorne/hinten (X-Enden).
- Kragen beginnt erst VORNE_FREI (2 cm) hinter der Vorderkante, läuft
  bis zum hinteren Ende durch.
- Kartenslots ganz vorne, beide im selben Y-Bereich (Kartenlänge
  85,6 mm liegt in Y - passt bequem), schmal in X, direkt hintereinander
  unmittelbar an der Vorderwand. Karten stehen aufrecht (bis zum Boden).
- Gesamtlänge (vorne->hinten) 11 cm (+1 cm Ablage hinten; Kragen bleibt
  wie bei 10 cm).

Bauen: ~/workspaces/cadquery/cadenv/bin/python teslabox.py
"""
import cadquery as cq
import math

# ---- Fach (NACHMESSEN) ---------------------------------------------
FALZ_BREITE  = 172.0     # Y, Öffnung oben, Aussenkante Falz
FALZ_TIEFE   = 4.0       # Absatztiefe (Stufenlehre)
FACH_BREITE  = 160.0     # Y, unterhalb des Falzes (Box 2mm je Seite schmaler; OY haengt nur von
                          # FALZ_BREITE/SPIEL_KRAGEN ab, Kragen-Absolutposition bleibt gleich)
FACH_TIEFE   = 95.0
ECK_RADIUS   = 4.0       # Rundung der Aussenkanten (deutlich reduziert)
SPIEL_KRAGEN = 0.5
SPIEL_KORPUS = 1.0

# ---- Einsatz ---------------------------------------------------------
# X +10 mm laenger als die Kragen-Referenz; Y/Z und Kragen unveraendert.
GESAMT_LAENGE_REF = 100.0  # Bezug fuer Kragen-Laenge (vor der Verlaengerung)
GESAMT_LAENGE = 110.0      # X, vorne->hinten (+10 mm gehen in die Ablage hinten)
VORNE_FREI    = 20.0     # X: kein Kragen in den ersten 2 cm ab vorne
KORPUS_HOEHE  = 84.0     # Gesamthöhe (Slot braucht 75mm Tiefe)
WAND, BODEN   = 2.6, 2.6
INNEN_FILLET, RIM_FILLET, FUSS_FILLET = 5.0, 1.0, 1.0

# ---- Kartenslots: nebeneinander, parallel zur Vorderseite ------------
# Slot-Öffnung (Y) läuft PARALLEL zur Vorderwand, direkt hintereinander
# in einer Linie. Schmal in X (Stapel von 10 Karten), tief in Z
# (aufrecht stehend) -> Z-Tiefe > X-Dicke ("tiefer als breit").
N_SLOT      = 2
SLOT_X_DICKE = 16.0      # X, Stapelbreite (~18-20 Karten a 0,76mm + Luft)
SLOT_Y_LAENGE = 66.0     # Y je Slot (+9mm, Kartenbreite 54mm + Luft, 6mm je Seite)
SLOT_TIEFE   = 80.0      # Z (Karte 85,6mm lang, steht ~5,6mm raus)
KARTEN_WAND  = 3.6
EINLAUF      = 3.0

# ---- Muenzbereich: Halbrohr-Rinne an der +Y-Seitenwand, ueber die
# Laenge der offenen Ablage (hinter dem Kartenblock bis zur Rueckwand).
# Sitzt oben am Rand, unten bleibt die Ablage frei nutzbar.
MUENZE_R      = 13.0     # Radius der Rundung unten (2-Euro-Muenze noch bequem)
MUENZE_GERADE = 8.0      # gerade, senkrechte Verlaengerung oben vor der Rundung -> mehr Tiefe
MUENZE_WAND   = 2.5      # Materialstaerke unter der Rundung
MUENZE_LIP    = 1.5      # kleiner Rand jeder Seite (verhindert tangentialen Boolean-Schnitt)
MUENZE_EMBED_VORNE = 2.0 # in die Kartenblock-Wand einbetten statt Luecke zu lassen (sonst fallen Muenzen durch)

# ---- Verjuengung unten: Fach wird nach unten enger (Klemmt nach ca. 1cm
# Einstecktiefe) -> Aussenwaende unterhalb des Kragens leicht konisch,
# damit der Korpus tiefer reinrutscht. Kragen selbst bleibt unangetastet.
BODEN_VERJUENGUNG = 10.0  # mm schmaler je Seite am Boden (1cm, klemmte vorher nach ca. 1cm)

# -----------------------------------------------------------------------
KL = GESAMT_LAENGE - 2 * SPIEL_KORPUS
KW = FACH_BREITE - 2 * SPIEL_KORPUS
OY = (FALZ_BREITE - FACH_BREITE) / 2 + SPIEL_KORPUS - SPIEL_KRAGEN
H  = KORPUS_HOEHE   # Kragen liegt IN der Oberkante, addiert keine Höhe
x_front, x_back = -KL / 2, KL / 2

def try_fillet(wp, sel, radii, what):
    for r in radii:
        try:
            return wp.edges(sel).fillet(r)
        except Exception:
            continue
    print(f"  ! fillet '{what}' uebersprungen")
    return wp

def try_chamfer(wp, sel, sizes, what):
    for c in sizes:
        try:
            return wp.edges(sel).chamfer(*c) if isinstance(c, tuple) else wp.edges(sel).chamfer(c)
        except Exception:
            continue
    print(f"  ! chamfer '{what}' uebersprungen")
    return wp

def try_fillet_edges(wp, edges, radii, what):
    for r in radii:
        try:
            return wp.newObject(edges).fillet(r)
        except Exception:
            continue
    print(f"  ! fillet '{what}' uebersprungen")
    return wp

# ---- Korpus + Kragen (nur ±Y, ab x_front+VORNE_FREI) ------------------
korpus = (cq.Workplane("XY").box(KL, KW, KORPUS_HOEHE, centered=(True, True, False))
          .edges("|Z").fillet(ECK_RADIUS))

def W(shape):
    return cq.Workplane("XY").add(shape)

# X-Bereich des Kragens: vorne Freibereich + 5mm mehr (Start 5mm weiter
# nach hinten verschoben). Laenge fest an GESAMT_LAENGE_REF gebunden, damit
# eine Box-Verlaengerung den Kragen nicht mitzieht (Extra -> hintere Ablage).
KRAGEN_START_EXTRA = 5.0
KL_REF = GESAMT_LAENGE_REF - 2 * SPIEL_KORPUS
klen = KL_REF - VORNE_FREI - KRAGEN_START_EXTRA - ECK_RADIUS
kx0 = x_front + VORNE_FREI + KRAGEN_START_EXTRA
kx1 = kx0 + klen
aussen = W(korpus.val())
ov = 1.0   # 1 mm in die Wand einbetten, sonst koinzidente Flächen -> Fuse-Fehler
# Unterkante des Kragens: gerade Wandseite bleibt voll dick, der Bereich
# dazwischen ist leicht schraeg angehoben (statt komplett waagrecht), und
# ganz an der Spitze bleibt eine kleine Rundung. Als Trapezprofil gebaut
# (nicht Box+Chamfer/Fillet auf Kontur), weil eine gewoehnliche <Z-Kontur
# nach dem Schraegen nicht mehr eindeutig "unten" ist. Nur die eine
# aussenliegende Kante behandeln (nicht die ganze Kontur) - sonst wird die
# Kragen/Korpus-Vereinigung durch zusaetzliche Eckkugel-Uebergaenge an den
# Streifenenden extrem langsam/haengt.
KRAGEN_SCHRAEG = 0.8   # mm Anstieg des geraden Bereichs zwischen Wand und Rundung
for y0, tip_at_max_y in ((KW / 2 - ov, True), (-KW / 2 - OY, False)):
    Wb = OY + ov
    if tip_at_max_y:
        pts = [(0, 0), (0, FALZ_TIEFE), (Wb, FALZ_TIEFE), (Wb, KRAGEN_SCHRAEG)]
    else:
        pts = [(0, KRAGEN_SCHRAEG), (0, FALZ_TIEFE), (Wb, FALZ_TIEFE), (Wb, 0)]
    strip = cq.Workplane("YZ").polyline(pts).close().extrude(klen)
    tip_y = Wb if tip_at_max_y else 0.0
    tip_candidates = [e for e in strip.edges("|X").vals() if abs(e.Center().y - tip_y) < 1e-6]
    tip_edge = min(tip_candidates, key=lambda e: e.Center().z)
    strip = try_fillet_edges(strip, [tip_edge], [1.5, 1.2, 1.0, 0.8, 0.6], "Kragen-Spitze")
    strip = strip.translate((kx0, y0, H - FALZ_TIEFE))   # buendig mit der Oberkante
    aussen = aussen.union(W(strip.val()))
aussen = W(aussen.val())   # zu einem sauberen Solid zusammenfassen

# Kartenblock: schmaler Streifen direkt an der Vorderwand, volle Höhe,
# bleibt massiv -> darin die 2 Slots nebeneinander (Y), parallel zur
# Vorderseite, in einer Linie (gleiches X).
block_x0 = x_front + WAND
block_xlen = SLOT_X_DICKE + 2 * KARTEN_WAND
block = (cq.Workplane("XY")
         .box(block_xlen, KW, H - BODEN + 20, centered=(False, True, False))
         .translate((block_x0, 0, BODEN)))   # überbreit in Y, wird von Kavität begrenzt

kavitaet = (cq.Workplane("XY").box(KL - 2 * WAND, KW - 2 * WAND, H - BODEN + 20, centered=(True, True, False))
            .translate((0, 0, BODEN))
            .cut(block)
            .edges("|Z").fillet(max(1.0, ECK_RADIUS - WAND))
            .edges("<Z").fillet(INNEN_FILLET))
teil = aussen.cut(kavitaet)

# ---- Kartenslots nebeneinander (Y), parallel zur Vorderseite ---------
gesamt_y = N_SLOT * SLOT_Y_LAENGE + (N_SLOT + 1) * KARTEN_WAND
y0 = -gesamt_y / 2
slot_y = [y0 + KARTEN_WAND * (i + 1) + SLOT_Y_LAENGE * (i + 0.5) for i in range(N_SLOT)]
xc = block_x0 + KARTEN_WAND + SLOT_X_DICKE / 2
st = SLOT_TIEFE if SLOT_TIEFE > 0 else (H - BODEN - 0.4)

SLOT_ECK = 1.2   # kleine Eckrundung am Slot statt voller Stadion-Rundung
for yc in slot_y:
    slot = (cq.Workplane("XY", origin=(xc, yc, H - st))
            .rect(SLOT_X_DICKE, SLOT_Y_LAENGE).extrude(st + 2)
            .edges("|Z").fillet(SLOT_ECK))
    teil = teil.cut(slot)
    if EINLAUF:
        funnel = (cq.Workplane("XY", origin=(xc, yc, H - EINLAUF))
                  .rect(SLOT_X_DICKE, SLOT_Y_LAENGE)
                  .workplane(offset=EINLAUF + 0.2)
                  .rect(SLOT_X_DICKE + 2 * EINLAUF, SLOT_Y_LAENGE + 2 * EINLAUF)
                  .loft(combine=False))
        teil = teil.cut(funnel)

# ---- Muenzrinne bauen und in die Ablage einsetzen ---------------------
muenze_y_wand = KW / 2 - WAND                          # Innenflaeche +Y-Wand
muenze_proj   = 2 * MUENZE_R + 2 * MUENZE_LIP           # wie weit sie hereinragt
muenze_y_c    = muenze_y_wand - MUENZE_LIP - MUENZE_R   # Rinnen-Mittelachse (Y)
# Vorne bis in die Kartenblock-Wand einbetten (keine Luecke mehr, durch die
# Muenzen in die Ablage fallen koennten); hinten bis an die Rueckwand.
muenze_x0     = block_x0 + block_xlen - MUENZE_EMBED_VORNE
muenze_x1     = x_back - WAND
muenze_z_top  = H
muenze_z_ax   = muenze_z_top - MUENZE_GERADE            # Kreiszentrum unter der geraden Strecke
muenze_bar_h  = MUENZE_GERADE + MUENZE_R + MUENZE_WAND
muenze_ov     = 3.5   # tiefer eingebettet als nur 1mm: die Verjuengung faengt gleich
                       # unter dem Kragen an (linear bis zum Boden) und schneidet daher
                       # auch in den Einbettungsbereich der -- viel tiefer reichenden --
                       # Muenzrinne; ohne mehr Einbett-Tiefe wuerde die Verbindung zur
                       # Wand am unteren Ende der Rinne auf <0,2mm duennlaufen (Risiko:
                       # Boolean trennt in 2 Solids, siehe cadquery-3d-printing Skill).
muenze_xlen   = muenze_x1 - muenze_x0 + 10

muenze_bar_w = muenze_proj + muenze_ov
# Gerader Keil, aber der Wand-Ansatzpunkt geht bewusst UNTER die urspruengliche
# Balkenhoehe hinunter (die Wand ist ja durchgehend bis zum Boden solide) -
# dadurch steht viel mehr Hoehe fuer den Keil zur Verfuegung, statt den Winkel
# auf die urspruengliche 23,5mm Balkenhoehe zu begrenzen. Bei 45 Grad bleiben
# am Kanalzentrum noch ~13mm Material (statt der vorher knappen <1mm bei einem
# Keil, der auf Balkenhoehe begrenzt war) - der Kanal selbst ist jetzt die
# einzige Grenze, nicht mehr der Keil. MUENZE_KEIL_TIEFE so gewaehlt, dass der
# Ansatzpunkt bei Z=muenze_z_top-muenze_bar_h-MUENZE_KEIL_TIEFE endet, deutlich
# oberhalb des Fachbodens (BODEN) - der Grossteil der Ablage bleibt frei.
MUENZE_KEIL_ANSTIEG = 4.0
MUENZE_KEIL_TIEFE = muenze_bar_w - MUENZE_KEIL_ANSTIEG   # ergibt 45 Grad
muenze_bar_pts = [(0, MUENZE_KEIL_ANSTIEG), (0, muenze_bar_h),
                   (muenze_bar_w, muenze_bar_h), (muenze_bar_w, -MUENZE_KEIL_TIEFE)]
muenze_bar = (cq.Workplane("YZ").polyline(muenze_bar_pts).close()
              .extrude(muenze_x1 - muenze_x0)
              .translate((muenze_x0, muenze_y_wand - muenze_proj, muenze_z_top - muenze_bar_h)))

# Schnittwerkzeug = gerades Rechteck oben (senkrechte Seitenwaende) +
# untere Kreishaelfte darunter (D-Form, flach oben/rund unten), damit die
# Rinne oben komplett offen ist (kein geschlossenes Rohr) und insgesamt
# tiefer wird als eine reine Halbkreis-Rinne.
muenze_gerade = (cq.Workplane("XY")
                  .box(muenze_xlen, 2 * MUENZE_R, MUENZE_GERADE, centered=(False, True, False))
                  .translate((muenze_x0 - 5, muenze_y_c, muenze_z_ax)))
muenze_cyl = (cq.Workplane("YZ", origin=(muenze_x0 - 5, muenze_y_c, muenze_z_ax))
              .circle(MUENZE_R).extrude(muenze_xlen))
muenze_oben = (cq.Workplane("XY")
               .box(muenze_xlen + 40, 4 * MUENZE_R, 4 * MUENZE_R, centered=(True, True, False))
               .translate((muenze_x0 - 15, muenze_y_c, muenze_z_ax)))
muenze_rund = W(muenze_cyl.val()).cut(W(muenze_oben.val()))
muenze_werkzeug = W(muenze_gerade.val()).union(W(muenze_rund.val()))
muenze_bar = muenze_bar.cut(W(muenze_werkzeug.val()))

teil = teil.union(W(muenze_bar.val()))

# ---- Verjuengung: Aussenwaende UND Kavitaet unterhalb des Kragens leicht
# konisch (gleiche Rate), damit die Wandstaerke konstant bleibt. Ohne die
# Kavitaet mitzuverjuengen wuerde die Wand bei 1cm/Seite Verjuengung am
# Boden negativ duenn/durchbrochen (nachgerechnet + isoliert getestet).
# Kragen-Zone (H-FALZ_TIEFE bis H) bleibt unangetastet.
# 1) Aussenkontur: Werkzeug zweiteilig (oben ueberdimensionierter Block
#    deckt Kragen/Oberkante ab, darunter Konus von KW bis KW-2*VERJUENGUNG)
#    per Intersect an "teil" angewendet.
# 2) Kavitaet-Ausgleich: die dadurch "zu weit" ausgehoehlte Kavitaet wird
#    mit der gleichen Rate wieder aufgefuellt (altes Kavitaet-Volumen minus
#    neuer, ebenso verjuengter Kavitaet-Kontur) und per Union ergaenzt.
# Geschuetzte (unverjuengte) Zone ist nur die 4mm Kragenhoehe selbst -
# Verjuengung soll linear direkt darunter bis zum Boden laufen (nicht erst
# ab der Muenzrinne). Die Rinne reicht tiefer als der Kragen und wird
# dadurch am unteren Ende leicht angeschnitten; das faengt die vergroesserte
# muenze_ov-Einbettung oben ab (siehe dort).
taper_start_z = H - FALZ_TIEFE
taper_angle = math.degrees(math.atan(BODEN_VERJUENGUNG / taper_start_z))
BIG = 10 * KW

taper_oben = (cq.Workplane("XY", origin=(0, 0, taper_start_z))
              .box(BIG, BIG, H - taper_start_z + 5, centered=(True, True, False)))
taper_konus = (cq.Workplane("XY", origin=(0, 0, taper_start_z))
               .rect(BIG, KW).extrude(-taper_start_z, taper=taper_angle))
taper_werkzeug = W(taper_oben.val()).union(W(taper_konus.val()))
teil = teil.intersect(W(taper_werkzeug.val()))

# WICHTIG: Aussengrenze des Fill-Stuecks muss der TATSAECHLICH verjuengten
# Aussenwand folgen (gleicher Konus) - nicht der alten geraden Kavitaets-
# grenze! Sonst ist das Fill-Stueck selbst eine gerade (unverjuengte) Wand,
# die dort wo sie breiter ist als die bereits verjuengte Aussenwand diese
# beim Union wieder ueberschreibt (= Bug 1: Verjuengung + gerade Wand
# gleichzeitig sichtbar/ueberlagert).
#
# ZWEITER FEHLER (behoben): extrude(taper=...) verjuengt BEIDE Dimensionen
# des Rechteck-Profils gleichzeitig, nicht nur die gewuenschte (Y). Mit
# rect(FILL_X, KW) waere auch FILL_X (die X-Tiefe der Kavitaet) mit
# verjuengt worden -> am Boden fehlten dadurch bis zu 20mm Material an der
# Vorder-/Rueckkante der Kavitaet (Loch gegenueber den Kartenslots). Fix:
# Konus mit ueberdimensioniertem BIG in X bauen (X bleibt praktisch
# unveraendert), danach separat mit einer NICHT verjuengten Box auf die
# echte X-Tiefe (FILL_X) zuschneiden.
INNEN_W = KW - 2 * WAND
FILL_X = KL - 2 * WAND
innen_konus = (cq.Workplane("XY", origin=(0, 0, taper_start_z))
               .rect(BIG, INNEN_W).extrude(-taper_start_z, taper=taper_angle))
fill_aussen_konus = (cq.Workplane("XY", origin=(0, 0, taper_start_z))
                      .rect(BIG, KW).extrude(-taper_start_z, taper=taper_angle))
verjuengung_fill = W(fill_aussen_konus.val()).cut(W(innen_konus.val()))
fill_x_clip = (cq.Workplane("XY", origin=(0, 0, taper_start_z))
               .box(FILL_X, BIG, taper_start_z, centered=(True, True, False))
               .translate((0, 0, -taper_start_z)))
verjuengung_fill = verjuengung_fill.intersect(W(fill_x_clip.val()))
teil = teil.union(W(verjuengung_fill.val()))

teil = try_fillet(teil, ">Z", [RIM_FILLET, 0.8, 0.6], "Oberkanten")
teil = try_fillet(teil, "<Z", [FUSS_FILLET, 0.8, 0.5], "Unterkante")

s = teil.val()
cq.exporters.export(s, "teslabox.stl")
schnitt = teil.cut(cq.Workplane("XY", origin=(0, 0, -5)).box(400, 400, 200, centered=(True, False, False)))
cq.exporters.export(schnitt.val(), "teslabox_schnitt.stl")

bb = s.BoundingBox()
print("teslabox.stl geschrieben")
print(f"  Aussen: {bb.xlen:.1f} x {bb.ylen:.1f} x {bb.zlen:.1f} mm")
print(f"  Kragen: ab {VORNE_FREI + KRAGEN_START_EXTRA:.0f} mm ab vorne bis {kx1 - x_front:.0f} mm (Laenge {klen:.0f} mm), {OY:.1f} mm breit, {FALZ_TIEFE:.1f} mm dick, beide Seiten")
print(f"  Slots (Y-Mitte) = {[round(y,1) for y in slot_y]} mm, Laenge {SLOT_Y_LAENGE} mm, Dicke {SLOT_X_DICKE} mm")
print(f"  Muenzrinne: X {muenze_x0:.0f} bis {muenze_x1:.0f} mm (Laenge {muenze_x1-muenze_x0:.0f} mm), Radius {MUENZE_R} mm, an +Y-Wand")
print(f"  Verjuengung: {BODEN_VERJUENGUNG:.1f} mm je Seite am Boden ({taper_angle:.1f} Grad, ab Z={taper_start_z:.0f} unter Kragen)")
print(f"  Solids: {len(s.Solids())}   (muss 1 sein)")
