from flask import Flask, jsonify, request, abort
import json
import os

app = Flask(__name__)
directory = "data"

with open(os.path.join(directory, 'productos.json'), 'r') as f:
    productos = json.load(f)
with open(os.path.join(directory, 'carrito.json'), 'r') as f:
    carritos_compra = json.load(f)
with open(os.path.join(directory, 'usuarios.json'), 'r') as f:
    usuarios = json.load(f)
with open(os.path.join(directory, 'ventas.json'), 'r') as f:
    ventas = json.load(f)

#CRUD Productos
@app.route('/productos', methods=['GET'])
def get_productos():
    return jsonify(productos)

@app.route('/productos/<int:id>', methods=['GET'])
def get_producto(id):
    producto = [producto for producto in productos if producto['id_producto'] == id]
    if len(producto) == 0:
        abort(404)
    return jsonify(producto[0])

@app.route('/productos', methods=['POST'])
def create_producto():
    if not request.json or not 'sku' in request.json or not 'nombre' in request.json:
        abort(400)

    producto = {
        'id_producto': productos[-1]['id_producto'] + 1,
        'sku': request.json['sku'],
        'nombre': request.json['nombre'],
        'descripcion': request.json.get('descripcion', ""),
        'numero_unidades': request.json.get('numero_unidades', 0),
        'precio_unitario': request.json.get('precio_unitario', 0)
    }
    productos.append(producto)
    with open('productos.json', 'w') as f:
        json.dump(productos, f, indent=4)
    return jsonify(producto), 201

@app.route('/productos/<int:id>', methods=['PUT'])
def update_producto(id):
    with open('productos.json', 'r') as f:
        productos = json.load(f)
    producto = [producto for producto in productos if producto['id_producto'] == id]
    if len(producto) == 0:
        abort(404)
    if not request.json:
        abort(400)
    producto[0]['sku'] = request.json.get('sku', producto[0]['sku'])
    producto[0]['nombre'] = request.json.get('nombre', producto[0]['nombre'])
    producto[0]['descripcion'] = request.json.get('descripcion', producto[0]['descripcion'])
    producto[0]['numero_unidades'] = request.json.get('numero_unidades', producto[0]['numero_unidades'])
    producto[0]['precio_unitario'] = request.json.get('precio_unitario', producto[0]['precio_unitario'])
    with open('productos.json', 'w') as f:
        json.dump(productos, f, indent=4)
    return jsonify(producto[0])

@app.route('/productos/<int:id>', methods=['DELETE']) # type: ignore
def delete_producto(id):
    with open('productos.json', 'r') as f:
        productos = json.load(f)
    producto = [producto for producto in productos if producto['id_producto'] == id]
    if len(producto) == 0:
        abort(404)
   
# CRUD CARRITO
# Obtener todos los carritos de compra
@app.route('/carritos_compra', methods=['GET'])
def get_carritos_compra():
    return jsonify(carritos_compra)

# Obtener un carrito de compra por su ID
@app.route('/carritos_compra/<int:id_carrito>', methods=['GET'])
def get_carrito_compra(id_carrito):
    carrito = None
    for c in carritos_compra:
        if c['id_carrito'] == id_carrito:
            carrito = c
            break
    return jsonify(carrito)

# Crear un nuevo carrito de compra
@app.route('/carritos_compra', methods=['POST'])
def create_carrito_compra():
    if not request.json:
        abort(400)
    new_carrito = {
        "id_carrito": request.json['id_carrito'], 
        "id_usuario": request.json['id_usuario'],
        "fecha": request.json['fecha'],
        "valor_total_compra": 0
    }
    carritos_compra.append(new_carrito)
    with open(os.path.join(directory, 'carrito.json'), 'w') as f:
        json.dump(carritos_compra, f, indent=4)
    return jsonify(new_carrito)

# Actualizar un carrito de compra existente
@app.route('/carritos_compra/<int:id_carrito>', methods=['PUT'])
def update_carrito_compra(id_carrito):
    if not request.json:
        abort(400)
    valor_total = 0
    for venta in ventas: 
        if(venta['id_carrito'] == id_carrito):
            valor_total += venta['valor_total']
    for c in carritos_compra:
        if c['id_carrito'] == id_carrito:
            c['id_usuario'] = request.json['id_usuario']
            c['fecha'] = request.json['fecha']
            c['valor_total_compra'] = valor_total
            with open(os.path.join(directory, 'carrito.json'), 'w') as file:
                json.dump(carritos_compra, file, indent=4)
            return jsonify(c)
    return jsonify({"message": "Carrito de compra no encontrado."})

# CRUD Ventas
# Ruta para obtener todas las ventas
@app.route('/ventas', methods=['GET'])
def get_ventas():
    return jsonify(ventas)

# Ruta para obtener una venta por su ID
@app.route('/ventas/<int:id_venta>', methods=['GET'])
def get_venta(id_venta):
    for venta in ventas['ventas']:
        if venta['id_venta'] == id_venta:
            return jsonify(venta)
    return jsonify({'message': 'Venta no encontrada'})

#Ruta para obtener las ventas del carrito de compra
@app.route('/ventas_carrito/<int:id_carrito>', methods=['GET'])
def get_carrito_venta(id_carrito):
    list = []
    for venta in ventas: 
        if(venta['id_carrito'] == id_carrito):
            venta['producto'] = [producto for producto in productos if producto['id_producto'] == venta['id_producto']]
            list.append(venta)
    return jsonify(list)

# Ruta para agregar una nueva venta
@app.route('/ventas', methods=['POST'])
def add_venta():
    if not request.json:
        abort(400)
    new_venta = request.json
    new_venta['id_venta'] = len(ventas) + 1
    # get the last index of carrito list
    new_venta['id_carrito'] = carritos_compra[len(carritos_compra)-1]['id_carrito']
    encontrado = False
    # Realiza una consulta de todos los productos y valida si comienza con EA, WE o SP.
    for producto in productos:
        if producto['id_producto'] == new_venta['id_producto'] and producto['numero_unidades'] >= new_venta['cantidad']:
            encontrado = True
            # Producto normal
            if producto['sku'].startswith('EA'):
                precio_neto = producto['precio_unitario'] * new_venta['cantidad'] 
            # Producto por peso 
            elif producto['sku'].startswith('WE'):
                # El precio unitario seria igual a la cantidad en kgs, solo que se ingresaria en el frontend.
                precio_neto = producto['precio_unitario'] * new_venta['cantidad']
            # Producto especial 
            else: 
                if new_venta['cantidad'] >= 3 and new_venta['cantidad'] <= 5:
                    precio_neto = producto['precio_unitario'] * new_venta['cantidad'] - (producto['precio_unitario'] * new_venta['cantidad'] * 0.2)
                elif new_venta['cantidad'] >= 6 and new_venta['cantidad'] <= 8:
                    precio_neto = producto['precio_unitario'] * new_venta['cantidad'] - (producto['precio_unitario'] * new_venta['cantidad'] * 0.4)
                elif new_venta['cantidad'] >= 9:
                    precio_neto = producto['precio_unitario'] * new_venta['cantidad'] - (producto['precio_unitario'] * new_venta['cantidad'] * 0.5)
                else:
                    precio_neto = producto['precio_unitario'] * new_venta['cantidad']
            break
    
    if encontrado == False: 
        return jsonify({'Error': 'La cantidad de productos supera el limite.'})
        
    new_venta['valor_total'] = precio_neto
    ventas.append(new_venta)
    with open(os.path.join(directory, 'ventas.json'), 'w') as f:
        json.dump(ventas, f, indent=4)
    return jsonify({'message': 'Venta agregada correctamente'})

# Ruta para actualizar una venta por su ID
@app.route('/ventas/<int:id_venta>', methods=['PUT'])
def update_venta(id_venta):
    for venta in ventas['ventas']:
        if venta['id_venta'] == id_venta:
            venta['id_producto'] = request.json['id_producto']
            venta['id_carrito'] = request.json['id_carrito']
            venta['cantidad'] = request.json['cantidad']
            venta['valor_total'] = request.json['valor_total']
            with open('ventas.json', 'w') as file:
                json.dump(ventas, file, indent=4)
            return jsonify({'message': 'Venta actualizada correctamente'})
    return jsonify({'message': 'Venta no encontrada'})

# Ruta para eliminar una venta por su ID
@app.route('/ventas/<int:id_venta>', methods=['DELETE'])
def delete_venta(id_venta):
    for venta in ventas:
        if venta['id_venta'] == id_venta:
            ventas.remove(venta)
            with open(os.path.join(directory, 'ventas.json'), 'w') as file:
                json.dump(ventas, file, indent=4)
            return jsonify({'message': 'Venta eliminada correctamente'})
    return jsonify({'message': 'La venta no ha sido encontrada'})

# INVENTARIO ACTUALIZADO DE PRODUCTOS DE UN CARRITO EN ESPECIFICO
@app.route('/inventario/<int:id_carrito>', methods=['GET'])
def get_inventario(id_carrito):
    list = []
    for venta in ventas: 
        if(venta['id_carrito'] == id_carrito):
            for producto in productos:
                if producto['id_producto'] == venta['id_producto']:
                    producto['numero_unidades'] = producto['numero_unidades'] - venta['cantidad']
                    list.append(producto)
        with open(os.path.join(directory, 'productos.json'), 'w') as file:
            json.dump(productos, file, indent=4)
    return ({'message':'Inventario actualizado', 'productos': list})
   
if __name__ == '__main__':
    app.run(debug=True)
