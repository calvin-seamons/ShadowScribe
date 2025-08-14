import React, { useState, useCallback, useMemo } from 'react';
import { 
  Image as ImageIcon, 
  Check, 
  X, 
  AlertTriangle, 
  CheckCircle, 
  Info,
  Eye,
  EyeOff,
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  RotateCcw
} from 'lucide-react';
import { ImageData } from '../../types';

interface PDFContentPreviewProps {
  images: ImageData[];
  onConfirm: (orderedImages: ImageData[]) => void;
  onReject: () => void;
  onImageReorder?: (newOrder: ImageData[]) => void;
  isLoading?: boolean;
}

interface ImageQualityIndicator {
  level: 'high' | 'medium' | 'low';
  color: string;
  icon: React.ReactNode;
  message: string;
  suggestions: string[];
}

export const PDFContentPreview: React.FC<PDFContentPreviewProps> = ({
  images,
  onConfirm,
  onReject,
  onImageReorder,
  isLoading = false
}) => {
  const [orderedImages, setOrderedImages] = useState<ImageData[]>(images);
  const [selectedImageIndex, setSelectedImageIndex] = useState(0);
  const [zoom, setZoom] = useState(1);
  const [showAllImages, setShowAllImages] = useState(false);

  // Calculate image quality indicators
  const qualityIndicator: ImageQualityIndicator = useMemo(() => {
    const indicators: Record<string, ImageQualityIndicator> = {
      high: {
        level: 'high',
        color: 'text-green-400',
        icon: <CheckCircle className="h-5 w-5" />,
        message: 'Excellent image quality detected',
        suggestions: [
          'Images are clear and high resolution',
          'Should process accurately with vision AI'
        ]
      },
      medium: {
        level: 'medium',
        color: 'text-yellow-400',
        icon: <AlertTriangle className="h-5 w-5" />,
        message: 'Good image quality with minor issues',
        suggestions: [
          'Images are readable but may have some clarity issues',
          'Vision processing should work well'
        ]
      },
      low: {
        level: 'low',
        color: 'text-red-400',
        icon: <AlertTriangle className="h-5 w-5" />,
        message: 'Poor image quality detected',
        suggestions: [
          'Images may be blurry or low resolution',
          'Consider using a higher quality PDF if available'
        ]
      }
    };
    
    // Simple quality assessment based on image dimensions
    const avgDimensions = orderedImages.reduce((sum, img) => sum + (img.dimensions.width * img.dimensions.height), 0) / orderedImages.length;
    const quality = avgDimensions > 1000000 ? 'high' : avgDimensions > 500000 ? 'medium' : 'low';
    return indicators[quality];
  }, [orderedImages]);

  // Image statistics
  const imageStats = useMemo(() => {
    const totalSize = orderedImages.reduce((total, image) => {
      const sizeBytes = (image.base64.length * 3) / 4;
      return total + sizeBytes;
    }, 0);
    
    return { 
      count: orderedImages.length, 
      totalSizeMB: totalSize / (1024 * 1024),
      avgWidth: Math.round(orderedImages.reduce((sum, img) => sum + img.dimensions.width, 0) / orderedImages.length),
      avgHeight: Math.round(orderedImages.reduce((sum, img) => sum + img.dimensions.height, 0) / orderedImages.length)
    };
  }, [orderedImages]);



  const handleConfirm = useCallback(() => {
    onConfirm(orderedImages);
  }, [orderedImages, onConfirm]);

  const handleZoomIn = useCallback(() => {
    setZoom(prev => Math.min(prev * 1.2, 3));
  }, []);

  const handleZoomOut = useCallback(() => {
    setZoom(prev => Math.max(prev / 1.2, 0.5));
  }, []);

  const handleResetZoom = useCallback(() => {
    setZoom(1);
  }, []);

  const handlePreviousImage = useCallback(() => {
    setSelectedImageIndex(prev => Math.max(0, prev - 1));
  }, []);

  const handleNextImage = useCallback(() => {
    setSelectedImageIndex(prev => Math.min(orderedImages.length - 1, prev + 1));
  }, [orderedImages.length]);

  const currentImage = orderedImages[selectedImageIndex];

  return (
    <div className="w-full max-w-6xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-white mb-2">Review PDF Images</h2>
          <p className="text-gray-400">
            Review the converted images from your PDF before proceeding to AI vision processing.
          </p>
        </div>
        <div className="flex items-center space-x-2">
          <button
            onClick={() => setShowAllImages(!showAllImages)}
            className="inline-flex items-center px-3 py-2 text-sm font-medium text-gray-300 hover:text-white transition-colors"
          >
            {showAllImages ? <Eye className="h-4 w-4 mr-2" /> : <EyeOff className="h-4 w-4 mr-2" />}
            {showAllImages ? 'Single View' : 'Show All'}
          </button>
        </div>
      </div>

      {/* Quality and Statistics Information */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Image Quality Indicator */}
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center mb-3">
            <div className={qualityIndicator.color}>
              {qualityIndicator.icon}
            </div>
            <h3 className="text-white font-medium ml-2">Image Quality</h3>
          </div>
          <p className={`text-sm mb-2 ${qualityIndicator.color}`}>
            {qualityIndicator.message}
          </p>
          <ul className="text-xs text-gray-400 space-y-1">
            {qualityIndicator.suggestions.map((suggestion, index) => (
              <li key={index}>• {suggestion}</li>
            ))}
          </ul>
        </div>

        {/* Image Statistics */}
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center mb-3">
            <ImageIcon className="h-5 w-5 text-purple-400" />
            <h3 className="text-white font-medium ml-2">Image Information</h3>
          </div>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div>
              <span className="text-gray-400">Pages:</span>
              <span className="text-white ml-2">{imageStats.count}</span>
            </div>
            <div>
              <span className="text-gray-400">Total Size:</span>
              <span className="text-white ml-2">{imageStats.totalSizeMB.toFixed(2)} MB</span>
            </div>
            <div>
              <span className="text-gray-400">Avg Width:</span>
              <span className="text-white ml-2">{imageStats.avgWidth}px</span>
            </div>
            <div>
              <span className="text-gray-400">Avg Height:</span>
              <span className="text-white ml-2">{imageStats.avgHeight}px</span>
            </div>
          </div>
        </div>
      </div>

      {/* Image Content */}
      {showAllImages ? (
        /* Grid View - Show All Images */
        <div className="bg-gray-800 rounded-lg p-4">
          <div className="flex items-center justify-between mb-4">
            <h3 className="text-white font-medium">All Pages</h3>
            <p className="text-sm text-gray-400">Click any image to view in detail</p>
          </div>
          <div className="grid grid-cols-2 md:grid-cols-3 lg:grid-cols-4 gap-4">
            {orderedImages.map((image, index) => (
              <div
                key={image.id}
                className="relative group cursor-pointer border-2 rounded-lg overflow-hidden transition-all border-gray-600 hover:border-gray-500"
                onClick={() => {
                  setSelectedImageIndex(index);
                  setShowAllImages(false);
                }}
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
                </div>
                <div className="absolute bottom-0 left-0 right-0 bg-black bg-opacity-75 text-white text-xs p-2">
                  <div className="flex justify-between">
                    <span>{image.dimensions.width} × {image.dimensions.height}</span>
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
                disabled={selectedImageIndex === 0}
                className="p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronLeft className="h-4 w-4" />
              </button>
              <span className="text-sm text-gray-400">
                {selectedImageIndex + 1} / {orderedImages.length}
              </span>
              <button
                onClick={handleNextImage}
                disabled={selectedImageIndex === orderedImages.length - 1}
                className="p-2 text-gray-400 hover:text-white disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <ChevronRight className="h-4 w-4" />
              </button>
              <div className="border-l border-gray-600 pl-2 ml-2 flex items-center space-x-1">
                <button
                  onClick={handleZoomOut}
                  className="p-2 text-gray-400 hover:text-white"
                >
                  <ZoomOut className="h-4 w-4" />
                </button>
                <span className="text-sm text-gray-400 min-w-[3rem] text-center">
                  {Math.round(zoom * 100)}%
                </span>
                <button
                  onClick={handleZoomIn}
                  className="p-2 text-gray-400 hover:text-white"
                >
                  <ZoomIn className="h-4 w-4" />
                </button>
                <button
                  onClick={handleResetZoom}
                  className="p-2 text-gray-400 hover:text-white"
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
                    transform: `scale(${zoom})`,
                    transformOrigin: 'top left'
                  }}
                />
              )}
            </div>
          </div>
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
            {orderedImages.length} image{orderedImages.length !== 1 ? 's' : ''} ready for vision processing
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
            <p className="text-blue-300 font-medium mb-1">Vision Processing Tips</p>
            <ul className="text-blue-200 text-sm space-y-1">
              <li>• Ensure all character sheet pages are clearly visible and readable</li>
              <li>• Check that text and numbers are legible in the images</li>
              <li>• The AI vision system works best with high-contrast, well-lit images</li>
              <li>• All images will be sent to GPT-4.1 for intelligent character data extraction</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
};