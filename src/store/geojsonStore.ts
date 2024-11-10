import { observable, action, computed, makeObservable } from "mobx";
import { GeoJsonObject } from "geojson";

interface GeoJsonFile {
    name: string;
    content: GeoJsonObject;
}

class GeoJsonStore {
    files: GeoJsonFile[] = [];
    selectedStage: string | null = null;
    trackIsVisible: boolean = false; // Состояние для видимости дорожек

    constructor() {
        // Здесь явно указываем, что это observable свойства и методы
        makeObservable(this, {
            files: observable,
            selectedStage: observable,
            trackIsVisible: observable,
            addFile: action,
            setSelectedStage: action,
            setTrackVisibility: action,
            resetState: action,
            filteredFiles: computed,
        });
    }

    // Метод для добавления файла
    addFile(fileName: string, content: GeoJsonObject) {
        this.files = [...this.files, { name: fileName, content }];
    }

    // Метод для установки выбранного этапа
    setSelectedStage(stage: string) {
        this.selectedStage = stage;
    }

    // Метод для установки видимости дорожек
    setTrackVisibility(isVisible: boolean) {
        this.trackIsVisible = isVisible;
    }

    // Метод для сброса состояния
    resetState() {
        this.selectedStage = null;
        this.trackIsVisible = false;
    }

    // Вычисляемое свойство для фильтрации файлов
    get filteredFiles() {
        if (this.selectedStage) {
            return this.files.filter((file) =>
                file.name.startsWith(this.selectedStage as string)
            );
        }
        return [];
    }

    // Метод для сброса состояния
    resetProject() {
        this.files = [];
        this.selectedStage = null;
        this.trackIsVisible = false;
    }
}

const geoJsonStore = new GeoJsonStore();
export default geoJsonStore;
