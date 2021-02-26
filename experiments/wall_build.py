import uuid
import time
import tempfile
from packages import ifcopenshell


def create_guid(): return ifcopenshell.guid.compress(uuid.uuid1().hex)


filename = 'modulize_wall.ifc'
timestamp = time.time()
timestring = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime(timestamp))
creator = "Richard Devegili"
organization = "Modulize? :)"
application, application_version = "IfcOpenShell", "0.5"
project_globalid, project_name = create_guid(), "Modulize Wall"

template = """ISO-10303-21;
HEADER;
FILE_DESCRIPTION(('ViewDefinition [CoordinationView]'),'2;1');
FILE_NAME('%(filename)s','%(timestring)s',('%(creator)s'),('%(organization)s'),'%(application)s','%(application)s','');
FILE_SCHEMA(('IFC2X3'));
ENDSEC;
DATA;
#1=IFCPERSON($,$,'%(creator)s',$,$,$,$,$);
#2=IFCORGANIZATION($,'%(organization)s',$,$,$);
#3=IFCPERSONANDORGANIZATION(#1,#2,$);
#4=IFCAPPLICATION(#2,'%(application_version)s','%(application)s','');
#5=IFCOWNERHISTORY(#3,#4,$,.ADDED.,$,#3,#4,%(timestamp)s);
#6=IFCDIRECTION((1.,0.,0.));
#7=IFCDIRECTION((0.,0.,1.));
#8=IFCCARTESIANPOINT((0.,0.,0.));
#9=IFCAXIS2PLACEMENT3D(#8,#7,#6);
#10=IFCDIRECTION((0.,1.,0.));
#11=IFCGEOMETRICREPRESENTATIONCONTEXT($,'Model',3,1.E-05,#9,#10);
#12=IFCDIMENSIONALEXPONENTS(0,0,0,0,0,0,0);
#13=IFCSIUNIT(*,.LENGTHUNIT.,$,.METRE.);
#14=IFCSIUNIT(*,.AREAUNIT.,$,.SQUARE_METRE.);
#15=IFCSIUNIT(*,.VOLUMEUNIT.,$,.CUBIC_METRE.);
#16=IFCSIUNIT(*,.PLANEANGLEUNIT.,$,.RADIAN.);
#17=IFCMEASUREWITHUNIT(IFCPLANEANGLEMEASURE(0.017453292519943295),#16);
#18=IFCCONVERSIONBASEDUNIT(#12,.PLANEANGLEUNIT.,'DEGREE',#17);
#19=IFCUNITASSIGNMENT((#13,#14,#15,#18));
#20=IFCPROJECT('%(project_globalid)s',#5,'%(project_name)s',$,$,$,$,(#11),#19);
ENDSEC;
END-ISO-10303-21;
""" % locals()

# Define template

temporary_handle, temporary_filename = tempfile.mkstemp(suffix=".ifc")
with open(temporary_filename, "wb") as file:
    file.write(template.encode())

# Get references to instances defined on the template

file = ifcopenshell.open(temporary_filename)

owner_history = file.by_type("IfcOwnerHistory")[0]
project = file.by_type("IfcProject")[0]
geometric_representation_context = file.by_type(
    "IfcGeometricRepresentationContext")[0]

point = 0., 0., 0.
dir1 = 0., 1., 0.
dir2 = 0., 0., 0.

# Creates an IfcAxis2Placement3D
# https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcgeometryresource/lexical/ifcaxis2placement3d.htm


def create_ifcaxis2placement(file, point=point, dir1=dir1, dir2=dir1):
    point = file.createIfcCartesianPoint(point)
    dir1 = file.createIfcDirection(dir1)
    dir2 = file.createIfcDirection(dir2)

    axis2placement = file.createIfcAxis2Placement3D(point, dir1, dir2)

    return axis2placement

# Creates an IfcLocalPlacement
# https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcgeometricconstraintresource/lexical/ifclocalplacement.htm


def create_ifclocalplacement(file, point=point, dir1=dir1, dir2=dir2, relative_to=None):
    axis2placement = create_ifcaxis2placement(file, point, dir1, dir2)

    site_localplacement = file.createIfcLocalPlacement(
        relative_to, axis2placement)

    return site_localplacement

# Creates an IfcPolyLine
# https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcgeometryresource/lexical/ifcpolyline.htm


def create_ifcpolyline(file, points):
    point_list = []

    for point in points:
        point = file.createIfcCartesianPoint(point)
        point_list.append(point)

    polyline = file.createIfcPolyLine(point_list)

    return polyline

# Creates an IfcExtrudedAreaSolid
# https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcgeometricmodelresource/lexical/ifcextrudedareasolid.htm


def create_ifcextrudedareasolid(file, points, ifcaxis2placement, extrude_direction, extrusion):
    polyline = create_ifcpolyline(file, points)

    arbitraryclosedprofiledef = file.createIfcArbitraryClosedProfileDef(
        "AREA", None, polyline)

    direction = file.createIfcDirection(extrude_direction)

    extrudedareasolid = file.createIfcExtrudedAreaSolid(
        arbitraryclosedprofiledef, ifcaxis2placement, direction, extrusion)

    return extrudedareasolid


# Here's where the magic happens!

site_localplacement = create_ifclocalplacement(file)

# https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcproductextension/lexical/ifcsite.htm

site = file.createIfcSite(create_guid(), owner_history, "Site", None, None,
                          site_localplacement, None, None, "ELEMENT", None, None, None, None, None)

building_localplacement = create_ifclocalplacement(
    file, relative_to=site_localplacement)

building = file.createIfcBuilding(create_guid(
), owner_history, 'Building', None, None, building_localplacement, None, None, "ELEMENT", None, None, None)

storey_localplacement = create_ifclocalplacement(
    file, relative_to=building_localplacement)

elevation = 0.0

buildingstorey = file.createIfcBuildingStorey(create_guid(
), owner_history, 'Building Storey', None, None, storey_localplacement, None, None, "ELEMENT", elevation)

container_storey = file.createIfcRelAggregates(create_guid(
), owner_history, "Building Container", None, building, [buildingstorey])

container_site = file.createIfcRelAggregates(
    create_guid(), owner_history, "Site Container", None, site, [building])

container_project = file.createIfcRelAggregates(
    create_guid(), owner_history, "Project Container", None, project, [site])

# Wall creation: Define the wall shape as a polyline axis and an extruded area solid
wall_placement = create_ifclocalplacement(
    file, relative_to=storey_localplacement)
polyline = create_ifcpolyline(file, [(0.0, 0.0, 0.0), (5.0, 0.0, 0.0)])
axis_representation = file.createIfcShapeRepresentation(
    geometric_representation_context, "Axis", "Curve2D", [polyline])

extrusion_placement = create_ifcaxis2placement(
    file, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
point_list_extrusion_area = [
    (0.0, -0.1, 0.0), (5.0, -0.1, 0.0), (5.0, 0.1, 0.0), (0.0, 0.1, 0.0), (0.0, -0.1, 0.0)]
solid = create_ifcextrudedareasolid(
    file, point_list_extrusion_area, extrusion_placement, (0.0, 0.0, 1.0), 3.0)
body_representation = file.createIfcShapeRepresentation(
    geometric_representation_context, "Body", "SweptSolid", [solid])

product_shape = file.createIfcProductDefinitionShape(
    None, None, [axis_representation, body_representation])

wall = file.createIfcWallStandardCase(create_guid(
), owner_history, "Wall", "An awesome wall", None, wall_placement, product_shape, None)


# Creates the wall material
# https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcmaterialresource/lexical/ifcmateriallayer.htm
# https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcmaterialresource/lexical/ifcmateriallayerset.htm
# https://standards.buildingsmart.org/IFC/RELEASE/IFC2x3/TC1/HTML/ifcmaterialresource/lexical/ifcmateriallayersetusage.htm

material = file.createIfcMaterial("Wall Material")
materiallayer = file.createIfcMaterialLayer(material, 0.3, None)
materiallayerset = file.createIfcMaterialLayerSet([materiallayer], None)
materiallayersetusage = file.createIfcMaterialLayerSetUsage(
    materiallayerset, "AXIS2", "POSITIVE", -0.1)

file.createIfcRelAssociatesMaterial(create_guid(), owner_history, RelatedObjects=[
    wall], RelatingMaterial=materiallayersetusage)

properties = [
    file.createIfcPropertySingleValue("Reference", "Reference", file.create_entity(
        "IfcText", "Describe the Reference"), None),
    file.createIfcPropertySingleValue(
        "IsExternal", "IsExternal", file.create_entity("IfcBoolean", True), None),
    file.createIfcPropertySingleValue(
        "ThermalTransmittance", "ThermalTransmittance", file.create_entity("IfcReal", 2.569), None),
    file.createIfcPropertySingleValue(
        "IntValue", "IntValue", file.create_entity("IfcInteger", 2), None)
]
propertyset = file.createIfcPropertySet(
    create_guid(), owner_history, "Pset_WallCommon", None, properties)

file.createIfcRelDefinesByProperties(
    create_guid(), owner_history, None, None, [wall], propertyset)

quantities = [
    file.createIfcQuantityLength(
        "Length", "Length of this beautiful wall!", None, 5.0),
    file.createIfcQuantityArea(
        "Area", "Area of the front face of this beautiful wall!", None, 5.0 * solid.Depth),
    file.createIfcQuantityVolume(
        "Volume", "Volume of this beautiful wall!", None, 5.0 * solid.Depth * materiallayer.LayerThickness)
]

elementquantity = file.createIfcElementQuantity(
    create_guid(), owner_history, "BaseQuantities", None, None, quantities)

file.createIfcRelDefinesByProperties(
    create_guid(), owner_history, None, None, [wall], elementquantity)

# TODO: Keep studying this part!

opening_placement = create_ifclocalplacement(
    file, (1.75, 0.0, 1.75), (1.0, 0.0, 1.0), (1.0, 0.0, 0.0), wall_placement)
opening_extrusion_placement = create_ifcaxis2placement(
    file, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
point_list_opening_extrusion_area = [
    (0.0, -0.1, 0.0), (1.0, -0.1, 0.0), (1.0, 0.1, 0.0), (0.0, 0.1, 0.0), (0.0, -0.1, 0.0)]
opening_solid = create_ifcextrudedareasolid(
    file, point_list_opening_extrusion_area, opening_extrusion_placement, (0.0, 0.0, 1.0), 1.0)
opening_representation = file.createIfcShapeRepresentation(
    geometric_representation_context, "Body", "SweptSolid", [opening_solid])
opening_shape = file.createIfcProductDefinitionShape(
    None, None, [opening_representation])
opening_element = file.createIfcOpeningElement(create_guid(
), owner_history, "Opening", "Don't get too close!", None, opening_placement, opening_shape, None)
file.createIfcRelVoidsElement(
    create_guid(), owner_history, None, None, wall, opening_element)

window_placement = create_ifclocalplacement(
    file, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0), opening_placement)
window_extrusion_placement = create_ifcaxis2placement(
    file, (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), (1.0, 0.0, 0.0))
point_list_window_extrusion_area = [
    (0.0, -0.01, 0.0), (1.0, -0.01, 0.0), (1.0, 0.01, 0.0), (0.0, 0.01, 0.0), (0.0, -0.01, 0.0)]
window_solid = create_ifcextrudedareasolid(
    file, point_list_window_extrusion_area, window_extrusion_placement, (0.0, 0.0, 1.0), 1.0)
window_representation = file.createIfcShapeRepresentation(
    geometric_representation_context, "Body", "SweptSolid", [window_solid])
window_shape = file.createIfcProductDefinitionShape(
    None, None, [window_representation])
window = file.createIfcWindow(create_guid(), owner_history, "Window",
                              "Can you see the other side?", None, window_placement, window_shape, None, None)

file.createIfcRelFillsElement(
    create_guid(), owner_history, None, None, opening_element, window)

file.createIfcRelContainedInSpatialStructure(create_guid(
), owner_history, "Building Storey Container", None, [wall, window], buildingstorey)

file.write(filename)
