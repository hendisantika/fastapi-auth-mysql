@app.post("/items/")
def create_item(item: Item):
    items.append(item)
    return {
        "message": "Item created successfully",
        "data": item
    }


@app.get("/items/")
def get_items():
    return items


@app.get("/items/{item_id}")
def get_item(item_id: int):
    for item in items:
        if item.id == item_id:
            return item

    return {"error": "Item not found"}
