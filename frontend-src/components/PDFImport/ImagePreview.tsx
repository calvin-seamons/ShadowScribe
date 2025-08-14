import React, { useState, useCallback, useMemo } from 'react';
import { 
  Check, 
  X, 
  RotateCcw, 
  ZoomIn, 
  ZoomOut, 
  ChevronLeft, 
  ChevronRight,
  Move,
  ArrowUp,
  ArrowDown,
  Eye,
  EyeOff,
  Info
} from 'lucide-react';
import { ImageData } from '../../types';

interface ImagePreviewProps {
  images: ImageData[];
  onConfirm: (orderedImages: ImageData[]) => void;
  onReject: () => void;
  onImageReorder?: (newOrder: ImageData[]) => void;
  isLoading?: boolean;
}

interface ImageViewState {
  selectedImageIndex: number;
  zoom: number;
  showAll: boolean;
}

export const ImagePreview: React.FC<ImagePreviewProps> = ({
  images,
  onConfirm,
  onReject,
  onImageReorder,
  isLoading = false
}) => {
  const [viewState, setViewState] = useState<ImageViewState>({
    selectedImageIndex: 0,
    zoom: 1,
    showAll: false
  });
  const [orderedImages, setOrderedImages] = useState<ImageData[]>(images);
  const [draggedIndex, setDraggedIndex] = useState<number | null>(null);

  // Calculate total size for display
  const totalSizeMB = useMemo(() => {
    return orderedImages.reduce((total, image) => {
      // Estimate size from base64 string length
      const sizeBytes = (image.base64.length * 3) / 4;
      return total + sizeBytes;
    }, 0) / (1024 * 1024);
  }, [orderedImages]);

  const handleImageReorder = useCallback((fromIndex: number, toIndex: number) => {
    const newOrder = [...orderedImages];
    const [movedImage] = newOrder.splice(fromIndex, 1);
    newOrder.splice(toIndex, 0, movedImage);
    
    setOrderedImages(newOrder);
    onImageReorder?.(newOrder);
    
    // Update selected index if needed
    if (viewState.selectedImageIndex === fromIndex) {
      setViewState(prev => ({ ...prev, selectedImageIndex: toIndex }));
    } else if (viewState.selectedImageIndex > fromIndex && viewState.selectedImageIndex <= toIndex) {
      setViewState(prev => ({ ...prev, selectedImageIndex: prev.selectedImageIndex - 1 }));
    } else if (viewState.selectedImageIndex < fromIndex && viewState.selectedImageIndex >= toIndex) {
      setViewState(prev => ({ ...prev, selectedImageIndex: prev.selectedImageIndex + 1 }));
    }
  }, [orderedImages, onImageReorder, viewState.selectedImageIndex]);

  const handleDragStart = useCallback((e: React.DragEvent, index: number) => {
    setDraggedIndex(index);
    e.dataTransfer.effectAllowed = 'move';
    e.dataTransfer.setData('text/html', '');
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    e.dataTransfer.dropEffect = 'move';
  }, []);

  const handleDrop = useCallback((e: React.DragEvent, dropIndex: number) => {
    e.preventDefault();
    if (draggedIndex !== null && draggedIndex !== dropIndex) {
      handleImageReorder(draggedIndex, dropIndex);
    }
    setDraggedIndex(null);
  }, [draggedIndex, handleImageReorder]);

  const handleMoveUp = useCallback((index: number) => {
    if (index > 0) {
      handleImageReorder(index, index - 1);
    }
  }, [handleImageReorder]);

  const handleMoveDown = useCallback((index: number) => {
    if (index < orderedImages.length - 1) {
      handleImageReorder(index, index + 1);
    }
  }, [handleImageReorder, orderedImages.length]);

  const handleZoomIn = useCallback(() => {
    setViewState(prev => ({ ...prev, zoom: Math.min(prev.zoom * 1.2, 3) }));
  }, []);

  const handleZoomOut = useCallback(() => {
    setViewState(prev => ({ ...prev, zoom: Math.max(prev.zoom / 1.2, 0.5) }));
  }, []);

  const handleResetZoom = useCallback(() => {
    setViewState(prev => ({ ...prev, zoom: 1 }));
  }, []);

  const handlePreviousImage = useCallback(() => {
    setViewState(prev => ({
      ...prev,
      selectedImageIndex: Math.max(0, prev.selectedImageIndex - 1)
    }));
  }, []);

  const handleNextImage = useCallback(() => {
    setViewState(prev => ({
      ...prev,
      selectedImageIndex: Math.min(orderedImages.length - 1, prev.selectedImageIndex + 1)
    }));
  }, [orderedImages.length]);

  const handleConfirm = useCallback(() => {
    onConfirm(orderedImages);
  }, [orderedImages, onConfirm]);

  const currentImage = orderedImages[viewState.selectedImageIndex];

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Review PDF Images</h2>
          <p className="text-gray-400">
            Review the converted images from your PDF. You can reorder pages and zoom in for details.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setViewState(prev => ({ ...prev, showAll: !prev.showAll }))}
            className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-300 hover:text-white transition-colors"
          >
            {viewState.showAll ? <Eye className="h-4 w-4 mr-2" /> : <EyeOff className="h-4 w-4 mr-2" />}
            {viewState.showAll ? 'Single View' : 'Show All'}
          </button>
        </div>
      </div>

      {/* Image Statistics */}
      <div className="bg-gray-800 rounded-lg p-4">
        <div className="flex items-center mb-3">
          <Info className="h-5 w-5 text-gray-400" />
          <h3 className="text-white font-medium ml-2">Image Information</h3>
        </div>
        <div className="grid grid-cols-3 gap-4 text-sm">
          <div>
            <span className="text-gray-400">Pages:</span>
            <span className="text-white ml-2">{orderedImages.length}</span>
          </div>
          <div>
            <span className="text-gray-400">Total Size:</span>
            <span className="text-white ml-2">{totalSizeMB.toFixed(2)} MB</span>
          </div>
          <div>
            <span className="text-gray-400">Format:</span>
            <span className="text-white ml-2">PNG/JPEG</span>
          </div>
        </div>
      </div>

      {viewState.showAll ? (
        /* Grid View - Show All Images */
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white font-medium">All Pages</h3>
            <p className="text-sm text-gray-400">Drag and drop to reorder</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {orderedImages.map((image, index) => (
              <div
                key={image.id}
                draggable
                onDragStart={(e) => handleDragStart(e, index)}
                onDragOver={handleDragOver}
                onDrop={(e) => handleDrop(e, index)}
                className={`relative group cursor-move border-2 rounded-lg overflow-hidden transition-all ${
                  draggedIndex === index 
                    ? 'border-purple-400 opacity-50' 
                    : 'border-gray-600 hover:border-gray-500'
                }`}
              >
                <img
                  src={image.base64}
                  alt={`Page ${image.pageNumber}`}
                  className="w-full h-48 object-contain bg-white"
                />
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all">
                  <div className="absolute top-2 left-2 bg-black bg-opacity-75 text-white text-xs px-2 py-1 rounded">
                    Page {image.pageNumber}
                  </div>
                  <div className="absolute top-2 right-2 opacity-0 group-hover:opacity-100 transition-opacity">
                    <div className="flex space-x-1">
                      <button
                        onClick={() => handleMoveUp(index)}
                        disabled={index === 0}
                        className="p-1 bg-black bg-opacity-75 text-white rounded hover:bg-opacity-100 disabled:opacity-50"
                      >
                        <ArrowUp className="h-3 w-3" />
                      </button>
                      <button
                        onClick={() => handleMoveDown(index)}
                        disabled={index === orderedImages.length - 1}
                        className="p-1 bg-black bg-opacity-75 text-white rounded hover:bg-opacity-100 disabled:opacity-50"
                      >
                        <ArrowDown className="h-3 w-3" />
                      </button>
                    </div>
                  </div>
                  <div className="absolute bottom-2 left-2 right-2">
                    <button
                      onClick={() => setViewState(prev => ({ ...prev, selectedImageIndex: index, showAll: false }))}
                      className="w-full py-1 bg-purple-600 bg-opacity-75 text-white text-xs rounded hover:bg-opacity-100 transition-all"
                    >
                      View Details
                    </button>
                  </div>
                </div>
                <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-75 text-white text-xs p-2">
                  <div className="flex justify-between">
                    <span>{image.dimensions.width} × {image.dimensions.height}</span>
                    <Move className="h-3 w-3" />
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      ) : (
        /* Single Image View */
        <div className="bg-gray-800 rounded-lg">
          <div className="flex items-center justify-between p-4 border-b border-gray-700">
            <div className="flex items-center space-x-4">
              <h3 className="text-white font-medium">
                Page {currentImage?.pageNumber} of {orderedImages.length}
              </h3>
              <div className="text-sm text-gray-400">
                {currentImage?.dimensions.width} × {currentImage?.dimensions.height}
              </div>
            </div>
            <div className="flex items-center space-x-2">
              <button
                onClick={handlePreviousImage}
                disabled={viewState.selectedImageIndex === 0}
                className="p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Previous image"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="text-sm text-gray-400">
                {viewState.selectedImageIndex + 1} / {orderedImages.length}
              </span>
              <button
                onClick={handleNextImage}
                disabled={viewState.selectedImageIndex === orderedImages.length - 1}
                className="p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
                aria-label="Next image"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
              <div className="border-l border-gray-600 pl-2 ml-2 flex items-center space-x-1">
                <button
                  onClick={handleZoomOut}
                  className="p-2 text-gray-400 hover:text-white"
                  aria-label="Zoom out"
                >
                  <ZoomOut className="h-4 w-4" />
                </button>
                <span className="text-sm text-gray-400 min-w-[3rem] text-center">
                  {Math.round(viewState.zoom * 100)}%
                </span>
                <button
                  onClick={handleZoomIn}
                  className="p-2 text-gray-400 hover:text-white"
                  aria-label="Zoom in"
                >
                  <ZoomIn className="h-4 w-4" />
                </button>
                <button
                  onClick={handleResetZoom}
                  className="p-2 text-gray-400 hover:text-white"
                  aria-label="Reset zoom"
                >
                  <RotateCcw className="h-4 w-4" />
                </button>
              </div>
            </div>
          </div>

          <div className="p-4">
            <div className="relative overflow-auto max-h-96 bg-gray-900 rounded border border-gray-600">
              {currentImage && (
                <img
                  src={currentImage.base64}
                  alt={`Page ${currentImage.pageNumber}`}
                  className="max-w-none bg-white"
                  style={{
                    transform: `scale(${viewState.zoom})`,
                    transformOrigin: 'top left'
                  }}
                />
              )}
            </div>
          </div>
        </div>
      )}

      {/* Page Order Controls */}
      {orderedImages.length > 1 && !viewState.showAll && (
        <div className="bg-gray-800 rounded-lg p-4">
          <h3 className="text-white font-medium mb-3">Page Order</h3>
          <div className="flex flex-wrap gap-2">
            {orderedImages.map((image, index) => (
              <div
                key={image.id}
                className={`relative group cursor-pointer border-2 rounded overflow-hidden transition-all ${
                  index === viewState.selectedImageIndex
                    ? 'border-purple-400'
                    : 'border-gray-600 hover:border-gray-500'
                }`}
                onClick={() => setViewState(prev => ({ ...prev, selectedImageIndex: index }))}
              >
                <img
                  src={image.base64}
                  alt={`Page ${image.pageNumber}`}
                  className="w-16 h-20 object-contain bg-white"
                />
                <div className="absolute inset-0 bg-black bg-opacity-0 group-hover:bg-opacity-20 transition-all">
                  <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-75 text-white text-xs p-1 text-center">
                    {image.pageNumber}
                  </div>
                </div>
              </div>
            ))}
          </div>
          <p className="text-xs text-gray-400 mt-2">
            Click to select • Switch to "Show All" view to drag and reorder pages
          </p>
        </div>
      )}

      {/* Action Buttons */}
      <div className="flex items-center justify-between pt-4">
        <button
          onClick={onReject}
          className="inline-flex items-center px-6 py-3 text-sm font-medium text-gray-300 bg-gray-700 hover:bg-gray-600 rounded-lg transition-colors"
        >
          <X className="h-4 w-4 mr-2" />
          Cancel Import
        </button>

        <div className="flex items-center space-x-3">
          <div className="text-sm text-gray-400">
            {orderedImages.length} page{orderedImages.length !== 1 ? 's' : ''} ready for processing
          </div>
          <button
            onClick={handleConfirm}
            disabled={isLoading || orderedImages.length === 0}
            className="inline-flex items-center px-6 py-3 text-sm font-medium text-white bg-purple-600 hover:bg-purple-700 rounded-lg transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
          >
            <Check className="h-4 w-4 mr-2" />
            Continue to Vision Processing
          </button>
        </div>
      </div>

      {/* Help Text */}
      <div className="bg-blue-900/20 border border-blue-700 rounded-lg p-4">
        <div className="flex items-start">
          <Info className="h-5 w-5 text-blue-400 mt-0.5 mr-3 flex-shrink-0" />
          <div>
            <p className="text-blue-300 font-medium mb-1">Image Review Tips</p>
            <ul className="text-blue-200 text-sm space-y-1">
              <li>• Ensure all character sheet pages are clearly visible and readable</li>
              <li>• Reorder pages if needed - character info should typically come first</li>
              <li>• Use zoom controls to check that text and numbers are legible</li>
              <li>• The AI vision system works best with high-contrast, well-lit images</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};