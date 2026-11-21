def product_to_dict(product):
    return {
        "codigo": product.code,
        "nombre": product.name,
        "descripcion": product.description,
        "categoria": product.category.name,
        "proveedor": product.supplier.name if product.supplier else None,
        "precio": product.price,
        "costo": product.cost,
        "margen_pct": product.margin(),
        "stock": product.stock,
        "stock_minimo": product.min_stock,
        "stock_bajo": product.is_low_stock(),
    }


def supplier_to_dict(supplier):
    return {
        "nombre": supplier.name,
        "contacto": supplier.contact_name,
        "tipo": supplier.supplier_type,
        "telefono": supplier.phone,
        "email": supplier.email,
        "direccion": supplier.address,
        "descripcion": supplier.description,
        "activo": supplier.is_active,
        "cantidad_productos": len(supplier.products),
    }
