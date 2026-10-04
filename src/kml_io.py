from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass
class Site:
    name: str
    lon: float
    lat: float
    altitude_m: float = 0.0


@dataclass
class KMLProject:
    boundary_name: str
    boundary_lonlat: list[tuple[float, float]]
    sites: list[Site]
    blockages: list[tuple[str, list[tuple[float, float]]]]


def _coords(text: str | None) -> list[tuple[float, float, float]]:
    if not text:
        return []
    out = []
    for token in text.replace("\n", " ").split():
        parts = token.split(",")
        if len(parts) >= 2:
            lon = float(parts[0])
            lat = float(parts[1])
            alt = float(parts[2]) if len(parts) >= 3 and parts[2] else 0.0
            out.append((lon, lat, alt))
    return out


def read_project(path: str | Path) -> KMLProject:
    path = Path(path)
    tree = ET.parse(path)
    root = tree.getroot()
    ns = {"k": "http://www.opengis.net/kml/2.2"}

    boundary_name = "Study Area"
    boundary = None
    sites: list[Site] = []
    blockages: list[tuple[str, list[tuple[float, float]]]] = []

    for pm in root.findall(".//k:Placemark", ns):
        name = (pm.findtext("k:name", default="Unnamed", namespaces=ns) or "Unnamed").strip()

        point_text = pm.findtext(".//k:Point/k:coordinates", default=None, namespaces=ns)
        if point_text:
            pts = _coords(point_text)
            if pts:
                lon, lat, alt = pts[0]
                if name.lower().startswith("gnb"):
                    sites.append(Site(name=name, lon=lon, lat=lat, altitude_m=alt))
            continue

        poly_text = pm.findtext(".//k:Polygon//k:outerBoundaryIs/k:LinearRing/k:coordinates", default=None, namespaces=ns)
        if poly_text:
            pts3 = _coords(poly_text)
            lonlat = [(p[0], p[1]) for p in pts3]
            lname = name.lower()
            if any(key in lname for key in ("blockage", "obstacle", "nlos", "che khuat", "che khuất")):
                blockages.append((name, lonlat))
            elif boundary is None:
                boundary = lonlat
                boundary_name = name

    if boundary is None:
        raise ValueError("No study-area Polygon found in KML.")
    if not sites:
        raise ValueError("No gNB Point placemarks found. Name points gNB-01, gNB-02, ...")

    sites.sort(key=lambda s: s.name)
    return KMLProject(boundary_name, boundary, sites, blockages)
