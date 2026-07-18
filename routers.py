@app.post("/items/")
def create_item(item: Item):
    items.append(item)
    return {
        "message": "Item created successfully",
        "data": item
    }
