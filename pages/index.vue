<template>
  <div class="min-h-screen bg-gray-100">
    <header class="bg-white shadow">
      <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <h1 class="text-3xl font-bold text-gray-900">衛星軌跡移除工具</h1>
      </div>
    </header>
    <main>
      <div class="max-w-7xl mx-auto py-6 sm:px-6 lg:px-8">
        <div class="bg-white shadow rounded-lg p-6 mb-6">
          <h2 class="text-xl font-semibold text-gray-900 mb-4">關於此工具</h2>
          <div class="prose max-w-none">
            <p class="text-gray-600 mb-4">
              這是一個專門用於移除天文照片中衛星軌跡的工具。當我們拍攝星空照片時，經常會遇到衛星經過留下的軌跡，這些軌跡會影響照片的品質和科學價值。
            </p>
            <h3 class="text-lg font-medium text-gray-900 mb-2">使用說明：</h3>
            <ul class="list-disc pl-5 text-gray-600 space-y-2">
              <li>上傳包含衛星軌跡的星空照片（支援 PNG、JPG、JPEG 格式）</li>
              <li>檔案大小限制為 10MB</li>
              <li>系統會自動識別並移除照片中的衛星軌跡</li>
              <li>處理完成後，您可以下載修復後的照片</li>
            </ul>
            <div class="mt-4 p-4 bg-blue-50 rounded-md">
              <p class="text-blue-700">
                <span class="font-semibold">注意：</span> 為了獲得最佳效果，請確保上傳的照片：
              </p>
              <ul class="list-disc pl-5 text-blue-700 mt-2">
                <li>具有足夠的解析度</li>
                <li>衛星軌跡清晰可見</li>
                <li>背景星空細節豐富</li>
              </ul>
            </div>
          </div>
        </div>

        <div class="px-4 py-6 sm:px-0">
          <div class="border-4 border-dashed border-gray-200 rounded-lg p-6">
            <div class="text-center">
              <div class="mt-1 flex justify-center px-6 pt-5 pb-6 border-2 border-gray-300 border-dashed rounded-md">
                <div class="space-y-1 text-center">
                  <svg class="mx-auto h-12 w-12 text-gray-400" stroke="currentColor" fill="none" viewBox="0 0 48 48" aria-hidden="true">
                    <path d="M28 8H12a4 4 0 00-4 4v20m32-12v8m0 0v8a4 4 0 01-4 4H12a4 4 0 01-4-4v-4m32-4l-3.172-3.172a4 4 0 00-5.656 0L28 28M8 32l9.172-9.172a4 4 0 015.656 0L28 28m0 0l4 4m4-24h8m-4-4v8m-12 4h.02" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" />
                  </svg>
                  <div class="flex text-sm text-gray-600">
                    <label for="file-upload" class="relative cursor-pointer bg-white rounded-md font-medium text-indigo-600 hover:text-indigo-500 focus-within:outline-none focus-within:ring-2 focus-within:ring-offset-2 focus-within:ring-indigo-500">
                      <span>上傳圖片</span>
                      <input id="file-upload" name="file-upload" type="file" class="sr-only" @change="handleFileUpload" accept="image/*">
                    </label>
                    <p class="pl-1">或拖放圖片到這裡</p>
                  </div>
                  <p class="text-xs text-gray-500">PNG, JPG, JPEG 最大 10MB</p>
                </div>
              </div>
            </div>
            
            <div v-if="selectedFile" class="mt-4">
              <div class="flex items-center justify-between">
                <div class="flex items-center">
                  <img :src="previewUrl" class="h-32 w-32 object-cover rounded" alt="預覽圖片">
                  <div class="ml-4">
                    <p class="text-sm font-medium text-gray-900">{{ selectedFile.name }}</p>
                    <p class="text-sm text-gray-500">{{ (selectedFile.size / 1024 / 1024).toFixed(2) }} MB</p>
                  </div>
                </div>
                <button @click="removeFile" class="text-red-600 hover:text-red-800">
                  <svg class="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                  </svg>
                </button>
              </div>
              <button 
                @click="uploadFile" 
                :disabled="isProcessing"
                class="mt-4 w-full bg-indigo-600 text-white py-2 px-4 rounded-md hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:ring-offset-2 disabled:opacity-50 disabled:cursor-not-allowed"
              >
                <span v-if="!isProcessing">開始處理</span>
                <span v-else class="flex items-center justify-center">
                  <svg class="animate-spin -ml-1 mr-3 h-5 w-5 text-white" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24">
                    <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4"></circle>
                    <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"></path>
                  </svg>
                  處理中...
                </span>
              </button>

              <!-- 進度條 -->
              <div v-if="isProcessing" class="mt-4">
                <div class="flex justify-between mb-1">
                  <span class="text-sm font-medium text-gray-700">處理進度</span>
                  <span class="text-sm font-medium text-gray-700">{{ progress }}%</span>
                </div>
                <div class="w-full bg-gray-200 rounded-full h-2.5">
                  <div 
                    class="bg-indigo-600 h-2.5 rounded-full transition-all duration-300 ease-in-out" 
                    :style="{ width: progress + '%' }"
                  ></div>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div v-if="processedImage" class="mt-8">
          <div class="bg-white shadow rounded-lg p-6">
            <h2 class="text-xl font-semibold text-gray-900 mb-4">處理結果</h2>
            <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
              <div class="space-y-2">
                <h3 class="text-lg font-medium text-gray-900">原始圖片</h3>
                <div class="relative aspect-square">
                  <img :src="previewUrl" class="w-full h-full object-contain rounded-lg" alt="原始圖片">
                </div>
              </div>
              
              <div class="space-y-2">
                <h3 class="text-lg font-medium text-gray-900">處理後圖片</h3>
                <div class="relative aspect-square">
                  <img :src="processedImage" class="w-full h-full object-contain rounded-lg" alt="處理後圖片">
                </div>
              </div>
            </div>

            <div class="mt-6 flex justify-center">
              <a 
                :href="processedImage" 
                download="processed_image.jpg"
                class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm text-white bg-indigo-600 hover:bg-indigo-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-indigo-500"
              >
                <svg class="mr-2 h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
                </svg>
                下載處理後圖片
              </a>
            </div>
          </div>
        </div>
      </div>
    </main>
    <footer class="bg-white border-t border-gray-200 mt-8">
      <div class="max-w-7xl mx-auto py-6 px-4 sm:px-6 lg:px-8">
        <div class="flex flex-col md:flex-row justify-between items-center">
          <div class="text-center md:text-left mb-4 md:mb-0">
            <p class="text-gray-500 text-sm">
              © 衛星軌跡移除工具
            </p>
          </div>
          <div class="flex space-x-6">
            <a href="https://github.com/xCk27x/satellite-trail-remover" class="text-gray-400 hover:text-gray-500">
              <span class="sr-only">GitHub</span>
              <svg class="h-6 w-6" fill="currentColor" viewBox="0 0 24 24">
                <path fill-rule="evenodd" d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z" clip-rule="evenodd" />
              </svg>
            </a>
          </div>
        </div>
        <div class="mt-4 text-center text-sm text-gray-500">

          <p class="mt-1">如有任何問題或建議，歡迎與我們聯繫</p>
        </div>
      </div>
    </footer>
  </div>
</template>

<script setup>
const selectedFile = ref(null)
const previewUrl = ref('')
const processedImage = ref('')
const isProcessing = ref(false)
const progress = ref(0)

const handleFileUpload = (event) => {
  const file = event.target.files[0]
  if (file) {
    if (file.size > 10 * 1024 * 1024) {
      alert('檔案大小不能超過 10MB')
      return
    }
    selectedFile.value = file
    previewUrl.value = URL.createObjectURL(file)
    processedImage.value = ''
    progress.value = 0
  }
}

const removeFile = () => {
  selectedFile.value = null
  previewUrl.value = ''
  processedImage.value = ''
  progress.value = 0
  isProcessing.value = false
}

const uploadFile = async () => {
  if (!selectedFile.value) return

  isProcessing.value = true
  progress.value = 0

  const formData = new FormData()
  formData.append('file', selectedFile.value)

  try {
    const response = await fetch('http://localhost:8000/process_image', {
      method: 'POST',
      body: formData
    })
    
    if (response.ok) {
      const result = await response.json()
      progress.value = 100
      
      // 更新圖片顯示
      if (result.images) {
        processedImage.value = result.images.final  // 使用最終處理後的圖片
      } else {
        throw new Error('未收到處理後的圖片')
      }
      
      isProcessing.value = false
    } else {
      throw new Error('處理失敗')
    }
  } catch (error) {
    console.error('上傳錯誤:', error)
    alert('上傳失敗，請確保後端服務正在運行')
    isProcessing.value = false
  }
}
</script> 