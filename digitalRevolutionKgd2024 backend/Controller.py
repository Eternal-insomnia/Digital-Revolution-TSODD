from fastapi import FastAPI, File, UploadFile
from fastapi.responses import JSONResponse
from GeojsonService import GeojsonService
import Graph
import pickle

app = FastAPI()
geojson_service = GeojsonService()

@app.post("/upload")
async def upload_multiple_shapefiles(
    shp_files: list[UploadFile] = File(...),
    shx_files: list[UploadFile] = File(...),
    dbf_files: list[UploadFile] = File(...),
    prj_files: list[UploadFile] = File(...),
    cpg_files: list[UploadFile] = File(...)
):
    response = await geojson_service.shp_to_geojson(shp_files, shx_files, dbf_files, prj_files, cpg_files)
    houses = geojson_service.merge_houses(response)
    buildings = geojson_service.add_base_objects(houses, response)
    roads = geojson_service.add_roads(houses, response)
    G = Graph.get_graph(buildings, roads)
    with open("graph.pkl", "wb") as f:
        pickle.dump(G, f)
    return JSONResponse(content={"geojson_files": G})


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=5557)
