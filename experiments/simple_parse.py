from packages import ifcopenshell
import os.path

filename = r'experiments\example_ifc_files\bosch_refrigeration_b36it800np.ifc'

file = ifcopenshell.open(filename)

products = file.by_type('IfcProduct')

print('Products of the imported IFC file:')

for product in products:
    product_info = product.get_info()

    product_id = product_info['id']
    product_name = product_info['Name']
    product_type = product_info['type']

    print(f'{product_name} ({product_id}) - {product_type}')
