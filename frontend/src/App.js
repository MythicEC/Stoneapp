import React, { useState, useEffect } from "react";
import "./App.css";
import axios from "axios";

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;
const API = `${BACKEND_URL}/api`;

function App() {
  const [activeTab, setActiveTab] = useState('upload');
  const [uploadedFile, setUploadedFile] = useState(null);
  const [uploading, setUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState(null);
  const [searchTerm, setSearchTerm] = useState('');
  const [searchType, setSearchType] = useState('all');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const [allOrders, setAllOrders] = useState([]);
  const [loading, setLoading] = useState(false);

  // Test API connection on mount
  useEffect(() => {
    const testConnection = async () => {
      try {
        const response = await axios.get(`${API}/`);
        console.log('API Connected:', response.data.message);
      } catch (error) {
        console.error('API Connection failed:', error);
      }
    };
    testConnection();
  }, []);

  // Load all orders when switching to orders tab
  useEffect(() => {
    if (activeTab === 'orders') {
      loadAllOrders();
    }
  }, [activeTab]);

  const loadAllOrders = async () => {
    try {
      setLoading(true);
      const response = await axios.get(`${API}/orders`);
      setAllOrders(response.data.orders);
    } catch (error) {
      console.error('Error loading orders:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleFileUpload = (event) => {
    const file = event.target.files[0];
    if (file && file.type === 'application/pdf') {
      setUploadedFile(file);
      setUploadResult(null);
    } else {
      alert('Bitte wählen Sie eine PDF-Datei aus.');
    }
  };

  const uploadPDF = async () => {
    if (!uploadedFile) return;

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', uploadedFile);

      const response = await axios.post(`${API}/upload-pdf`, formData, {
        headers: {
          'Content-Type': 'multipart/form-data',
        },
      });

      setUploadResult(response.data);
      setUploadedFile(null);
      // Reset file input
      document.getElementById('file-input').value = '';
    } catch (error) {
      console.error('Upload error:', error);
      alert(error.response?.data?.detail || 'Fehler beim Hochladen');
    } finally {
      setUploading(false);
    }
  };

  const searchOrders = async () => {
    if (!searchTerm.trim()) return;

    try {
      setSearching(true);
      const response = await axios.post(`${API}/search-orders`, {
        search_term: searchTerm,
        search_type: searchType
      });

      setSearchResults(response.data.results);
    } catch (error) {
      console.error('Search error:', error);
      alert('Fehler bei der Suche');
    } finally {
      setSearching(false);
    }
  };

  const deleteOrder = async (orderId) => {
    if (!window.confirm('Sind Sie sicher, dass Sie diesen Auftrag löschen möchten?')) {
      return;
    }

    try {
      await axios.delete(`${API}/order/${orderId}`);
      // Refresh orders list
      if (activeTab === 'orders') {
        loadAllOrders();
      }
      // Clear search results if the deleted order was in search results
      setSearchResults(results => results.filter(order => order.id !== orderId));
    } catch (error) {
      console.error('Delete error:', error);
      alert('Fehler beim Löschen');
    }
  };

  const formatDate = (dateString) => {
    return new Date(dateString).toLocaleDateString('de-DE', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    });
  };

  const OrderCard = ({ order, showDelete = true }) => (
    <div className="bg-white rounded-lg shadow-md p-6 border-l-4 border-stone-600">
      <div className="flex justify-between items-start mb-4">
        <div>
          <h3 className="text-lg font-semibold text-stone-800">
            {order.order_number}
          </h3>
          <p className="text-stone-600">{order.customer_name}</p>
        </div>
        {showDelete && (
          <button
            onClick={() => deleteOrder(order.id)}
            className="text-red-600 hover:text-red-800 text-sm font-medium"
          >
            Löschen
          </button>
        )}
      </div>
      
      <div className="space-y-2">
        <div className="flex items-center">
          <span className="font-medium text-stone-700 w-20">Steinart:</span>
          <span className="text-stone-600">{order.stone_type}</span>
        </div>
        <div className="flex items-center">
          <span className="font-medium text-stone-700 w-20">Datum:</span>
          <span className="text-stone-600">{formatDate(order.upload_date)}</span>
        </div>
      </div>
    </div>
  );

  return (
    <div className="min-h-screen bg-gradient-to-br from-stone-100 to-stone-200">
      {/* Hero Section */}
      <div 
        className="relative bg-cover bg-center h-64"
        style={{
          backgroundImage: "linear-gradient(rgba(0,0,0,0.6), rgba(0,0,0,0.6)), url('https://images.unsplash.com/photo-1652305461546-bf0a76934433?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2NzB8MHwxfHNlYXJjaHwxfHxncmFuaXRlfGVufDB8fHx8MTc1MzE5NDQyM3ww&ixlib=rb-4.1.0&q=85')"
        }}
      >
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center text-white">
            <h1 className="text-4xl font-bold mb-2">Steinmetz Auftragsverwaltung</h1>
            <p className="text-xl">Verwalten Sie Ihre Aufträge digital und effizient</p>
          </div>
        </div>
      </div>

      <div className="container mx-auto px-4 py-8">
        {/* Navigation Tabs */}
        <div className="flex space-x-1 mb-8 bg-white rounded-lg p-1 shadow-md">
          <button
            onClick={() => setActiveTab('upload')}
            className={`flex-1 py-3 px-4 rounded-md text-center font-medium transition-colors ${
              activeTab === 'upload' 
                ? 'bg-stone-600 text-white' 
                : 'text-stone-600 hover:bg-stone-100'
            }`}
          >
            📄 PDF Hochladen
          </button>
          <button
            onClick={() => setActiveTab('search')}
            className={`flex-1 py-3 px-4 rounded-md text-center font-medium transition-colors ${
              activeTab === 'search' 
                ? 'bg-stone-600 text-white' 
                : 'text-stone-600 hover:bg-stone-100'
            }`}
          >
            🔍 Aufträge Suchen
          </button>
          <button
            onClick={() => setActiveTab('orders')}
            className={`flex-1 py-3 px-4 rounded-md text-center font-medium transition-colors ${
              activeTab === 'orders' 
                ? 'bg-stone-600 text-white' 
                : 'text-stone-600 hover:bg-stone-100'
            }`}
          >
            📋 Alle Aufträge
          </button>
        </div>

        {/* Upload Tab */}
        {activeTab === 'upload' && (
          <div className="max-w-2xl mx-auto">
            <div className="bg-white rounded-lg shadow-lg p-8">
              <h2 className="text-2xl font-bold text-stone-800 mb-6 text-center">
                PDF Auftrag hochladen
              </h2>
              
              <div className="mb-6">
                <label className="block text-stone-700 font-medium mb-2">
                  PDF-Datei auswählen
                </label>
                <input
                  id="file-input"
                  type="file"
                  accept=".pdf"
                  onChange={handleFileUpload}
                  className="w-full p-3 border-2 border-stone-300 rounded-lg focus:border-stone-600 focus:outline-none"
                />
              </div>

              {uploadedFile && (
                <div className="mb-6 p-4 bg-stone-50 rounded-lg">
                  <p className="text-stone-700">
                    <strong>Ausgewählte Datei:</strong> {uploadedFile.name}
                  </p>
                  <p className="text-stone-600 text-sm">
                    Größe: {(uploadedFile.size / 1024 / 1024).toFixed(2)} MB
                  </p>
                </div>
              )}

              <button
                onClick={uploadPDF}
                disabled={!uploadedFile || uploading}
                className="w-full bg-stone-600 text-white py-3 px-6 rounded-lg font-medium hover:bg-stone-700 disabled:bg-stone-300 disabled:cursor-not-allowed transition-colors"
              >
                {uploading ? 'Hochladen...' : 'PDF Hochladen'}
              </button>

              {uploadResult && (
                <div className="mt-6 p-4 bg-green-50 border border-green-200 rounded-lg">
                  <h3 className="font-semibold text-green-800 mb-2">Erfolgreich hochgeladen!</h3>
                  <div className="space-y-1 text-green-700">
                    <p><strong>Auftragsnummer:</strong> {uploadResult.extracted_info.order_number}</p>
                    <p><strong>Kunde:</strong> {uploadResult.extracted_info.customer_name}</p>
                    <p><strong>Steinart:</strong> {uploadResult.extracted_info.stone_type}</p>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {/* Search Tab */}
        {activeTab === 'search' && (
          <div className="max-w-4xl mx-auto">
            <div className="bg-white rounded-lg shadow-lg p-8 mb-6">
              <h2 className="text-2xl font-bold text-stone-800 mb-6 text-center">
                Aufträge durchsuchen
              </h2>
              
              <div className="flex flex-col md:flex-row gap-4 mb-6">
                <input
                  type="text"
                  value={searchTerm}
                  onChange={(e) => setSearchTerm(e.target.value)}
                  placeholder="Suchbegriff eingeben..."
                  className="flex-1 p-3 border-2 border-stone-300 rounded-lg focus:border-stone-600 focus:outline-none"
                  onKeyPress={(e) => e.key === 'Enter' && searchOrders()}
                />
                
                <select
                  value={searchType}
                  onChange={(e) => setSearchType(e.target.value)}
                  className="p-3 border-2 border-stone-300 rounded-lg focus:border-stone-600 focus:outline-none bg-white"
                >
                  <option value="all">Alle Felder</option>
                  <option value="order_number">Auftragsnummer</option>
                  <option value="customer_name">Kundenname</option>
                  <option value="stone_type">Steinart</option>
                </select>
                
                <button
                  onClick={searchOrders}
                  disabled={searching || !searchTerm.trim()}
                  className="px-6 py-3 bg-stone-600 text-white rounded-lg font-medium hover:bg-stone-700 disabled:bg-stone-300 disabled:cursor-not-allowed transition-colors"
                >
                  {searching ? 'Suchen...' : 'Suchen'}
                </button>
              </div>
            </div>

            {/* Search Results */}
            {searchResults.length > 0 && (
              <div>
                <h3 className="text-xl font-bold text-stone-800 mb-4">
                  Suchergebnisse ({searchResults.length})
                </h3>
                <div className="grid gap-4">
                  {searchResults.map((order) => (
                    <OrderCard key={order.id} order={order} />
                  ))}
                </div>
              </div>
            )}

            {searchTerm && searchResults.length === 0 && !searching && (
              <div className="text-center text-stone-600 py-8">
                Keine Aufträge gefunden für "{searchTerm}"
              </div>
            )}
          </div>
        )}

        {/* All Orders Tab */}
        {activeTab === 'orders' && (
          <div className="max-w-4xl mx-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-2xl font-bold text-stone-800">
                Alle Aufträge ({allOrders.length})
              </h2>
              <button
                onClick={loadAllOrders}
                disabled={loading}
                className="px-4 py-2 bg-stone-600 text-white rounded-lg font-medium hover:bg-stone-700 disabled:bg-stone-300 transition-colors"
              >
                {loading ? 'Laden...' : 'Aktualisieren'}
              </button>
            </div>

            {loading ? (
              <div className="text-center text-stone-600 py-8">
                Lade Aufträge...
              </div>
            ) : allOrders.length > 0 ? (
              <div className="grid gap-4">
                {allOrders.map((order) => (
                  <OrderCard key={order.id} order={order} />
                ))}
              </div>
            ) : (
              <div className="text-center text-stone-600 py-8">
                Noch keine Aufträge vorhanden.
              </div>
            )}
          </div>
        )}
      </div>

      {/* Footer */}
      <div 
        className="mt-16 bg-cover bg-center py-16"
        style={{
          backgroundImage: "linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url('https://images.unsplash.com/photo-1673865641469-34498379d8af?crop=entropy&cs=srgb&fm=jpg&ixid=M3w3NTY2Njd8MHwxfHNlYXJjaHwyfHxtYXNvbnJ5fGVufDB8fHx8MTc1MzE5NDQ0MXww&ixlib=rb-4.1.0&q=85')"
        }}
      >
        <div className="text-center text-white">
          <h3 className="text-2xl font-bold mb-2">Professionelle Steinmetzarbeiten</h3>
          <p className="text-lg">Qualität und Handwerkskunst seit Generationen</p>
        </div>
      </div>
    </div>
  );
}

export default App;