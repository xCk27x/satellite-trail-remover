import { defineEventHandler, readMultipartFormData } from 'h3'
import { writeFile } from 'fs/promises'
import { join } from 'path'
import { mkdir } from 'fs/promises'
import { exec } from 'child_process'
import { promisify } from 'util'
import { readFile, unlink } from 'fs/promises'
import { randomUUID } from 'crypto'

const execAsync = promisify(exec)

// 設定檔案大小限制（10MB）
const MAX_FILE_SIZE = 10 * 1024 * 1024

// 建立處理佇列
const processingQueue = new Map()

export default defineEventHandler(async (event) => {
  const requestId = randomUUID() // 為每個請求生成唯一ID
  let inputPath = ''
  let outputPath = ''

  try {
    const formData = await readMultipartFormData(event)
    if (!formData) {
      throw new Error('沒有收到檔案')
    }

    const file = formData.find(item => item.name === 'image')
    if (!file) {
      throw new Error('找不到圖片檔案')
    }

    // 檢查檔案大小
    if (file.data.length > MAX_FILE_SIZE) {
      throw new Error(`檔案大小超過限制（最大 ${MAX_FILE_SIZE / (1024 * 1024)}MB）`)
    }

    // 建立上傳目錄（如果不存在）
    const uploadDir = join(process.cwd(), 'uploads')
    await mkdir(uploadDir, { recursive: true })

    // 使用 UUID 產生唯一的檔案名稱
    const inputFileName = `${requestId}-${file.filename}`
    const outputFileName = `processed-${inputFileName}`
    inputPath = join(uploadDir, inputFileName)
    outputPath = join(uploadDir, outputFileName)

    // 將請求加入處理佇列
    processingQueue.set(requestId, {
      status: 'processing',
      startTime: Date.now()
    })

    // 儲存上傳的檔案
    await writeFile(inputPath, file.data)

    // 執行 Python 腳本處理圖片
    const pythonScript = join(process.cwd(), 'server', 'process_image.py')
    const { stdout, stderr } = await execAsync(`python ${pythonScript} "${inputPath}" "${outputPath}"`)

    if (stderr) {
      console.error(`Python 腳本錯誤 (Request ID: ${requestId}):`, stderr)
      throw new Error('處理圖片時發生錯誤')
    }

    // 檢查輸出文件是否存在
    try {
      await readFile(outputPath)
    } catch (error) {
      console.error(`無法讀取處理後的圖片 (Request ID: ${requestId}):`, error)
      throw new Error('處理後的圖片不存在')
    }

    // 讀取處理後的圖片
    const processedImage = await readFile(outputPath)
    const base64Image = processedImage.toString('base64')

    // 更新處理狀態
    processingQueue.set(requestId, {
      status: 'completed',
      endTime: Date.now()
    })

    return {
      success: true,
      message: '圖片處理成功',
      image: `data:image/jpeg;base64,${base64Image}`,
      requestId
    }
  } catch (error) {
    // 更新處理狀態為失敗
    processingQueue.set(requestId, {
      status: 'failed',
      error: error instanceof Error ? error.message : '未知錯誤',
      endTime: Date.now()
    })

    console.error(`處理檔案時發生錯誤 (Request ID: ${requestId}):`, error)
    return {
      success: false,
      message: error instanceof Error ? error.message : '處理檔案時發生錯誤',
      requestId
    }
  }
  // finally {
  //   // 清理檔案
  //   try {
  //     if (inputPath) {
  //       try {
  //         await unlink(inputPath)
  //       } catch (error) {
  //         console.error(`清理輸入檔案時發生錯誤 (Request ID: ${requestId}):`, error)
  //       }
  //     }
  //     if (outputPath) {
  //       try {
  //         await unlink(outputPath)
  //       } catch (error) {
  //         console.error(`清理輸出檔案時發生錯誤 (Request ID: ${requestId}):`, error)
  //       }
  //     }
  //   } catch (error) {
  //     console.error(`清理檔案時發生錯誤 (Request ID: ${requestId}):`, error)
  //   }

  //   // 從處理佇列中移除
  //   processingQueue.delete(requestId)
  // }
}) 