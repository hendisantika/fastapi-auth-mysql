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
