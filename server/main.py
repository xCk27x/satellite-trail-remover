import torch
from torch.utils.data import DataLoader
import os
import numpy as np
from dsr_model import SubspaceRestrictionModule, ImageReconstructionNetwork, AnomalyDetectionModule
from discrete_model import DiscreteLatentModel
from sklearn.metrics import roc_auc_score, average_precision_score
from data_loader_test import TestMVTecDataset
import cv2
from fastapi import FastAPI, UploadFile, File
from fastapi.middleware.cors import CORSMiddleware
from PIL import Image
import io
import logging
from datetime import datetime, timedelta
import uuid
from fastapi.responses import FileResponse
from fastapi import HTTPException
import shutil
import threading
import time

# 設置 logger
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 創建文件處理器
file_handler = logging.FileHandler('app.log')
file_handler.setLevel(logging.INFO)

# 創建控制台處理器
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# 創建格式化器
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
console_handler.setFormatter(formatter)

# 添加處理器到 logger
logger.addHandler(file_handler)
logger.addHandler(console_handler)

app = FastAPI()

# 配置 CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 圖片保留時間（小時）
IMAGE_RETENTION_HOURS = 1

def cleanup_old_files():
    """清理超過保留時間的檔案"""
    while True:
        try:
            upload_dir = './uploads'
            current_time = datetime.now()
            
            # 遍歷 uploads 目錄及其子目錄
            for root, dirs, files in os.walk(upload_dir):
                for file in files:
                    file_path = os.path.join(root, file)
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    # 如果檔案超過保留時間，則刪除
                    if current_time - file_time > timedelta(hours=IMAGE_RETENTION_HOURS):
                        try:
                            os.remove(file_path)
                            logger.info(f"已刪除過期檔案: {file_path}")
                        except Exception as e:
                            logger.error(f"刪除檔案時出錯: {file_path}, 錯誤: {str(e)}")
            
            # 檢查並刪除空目錄
            for root, dirs, files in os.walk(upload_dir, topdown=False):
                for dir in dirs:
                    dir_path = os.path.join(root, dir)
                    if not os.listdir(dir_path):
                        try:
                            os.rmdir(dir_path)
                            logger.info(f"已刪除空目錄: {dir_path}")
                        except Exception as e:
                            logger.error(f"刪除目錄時出錯: {dir_path}, 錯誤: {str(e)}")
        
        except Exception as e:
            logger.error(f"清理檔案時發生錯誤: {str(e)}")
        
        # 每小時執行一次清理
        time.sleep(3600)

# 啟動清理線程
cleanup_thread = threading.Thread(target=cleanup_old_files, daemon=True)
cleanup_thread.start()

# 模型參數
NUM_HIDDENS = 128
NUM_RESIDUAL_HIDDENS = 64
NUM_RESIDUAL_LAYERS = 2
EMBEDDING_DIM = 128
NUM_EMBEDDINGS = 4096
COMMITMENT_COST = 0.25
DECAY = 0.99



def crop_image(image, img_dim):
    b,c,h,w = image.shape
    hdif = max(0,h - img_dim) // 2
    wdif = max(0,w - img_dim) // 2
    image_cropped = image[:,:,hdif:-hdif,wdif:-wdif]
    return image_cropped

def evaluate_model(model, model_normal, model_normal_top, model_decode, decoder_seg, model_upsample, obj_name, mvtec_path, cnt_total):
    list1 = []
    img_dim = 256
    dataset = TestMVTecDataset(mvtec_path, resize_shape=[img_dim,img_dim])
    dataloader = DataLoader(dataset, batch_size=1, shuffle=False, num_workers=0)

    img_dim = 224
    total_pixel_scores = np.zeros((img_dim * img_dim * 500))
    total_gt_pixel_scores = np.zeros((img_dim * img_dim * 500))
    mask_cnt = 0

    total_gt = []
    total_score = []
    iter = cnt_total

    for i_batch, sample_batched in enumerate(dataloader):

        gray_batch = sample_batched["image"]
        gray_batch2 = gray_batch.detach().cpu().numpy()
        gray_batch2 = np.squeeze(gray_batch2)
        gray_batch2 = np.transpose(gray_batch2, (1, 2, 0)) * 255
        # print(gray_batch)
        
        is_normal = sample_batched["has_anomaly"].detach().numpy()[0,0]
        
        total_gt.append(is_normal)
        true_mask = sample_batched["mask"]
        true_mask = crop_image(true_mask, img_dim)
        true_mask_cv = true_mask.detach().numpy()[0, :, :, :].transpose((1, 2, 0))

        loss_b, loss_t, data_recon, embeddings_t, embeddings = model(gray_batch)
        embeddings = embeddings.detach()
        embeddings_t = embeddings_t.detach()

        embedder = model._vq_vae_bot
        embedder_top = model._vq_vae_top

        anomaly_embedding_copy = embeddings.clone()
        anomaly_embedding_top_copy = embeddings_t.clone()
        recon_feat, recon_embeddings, _ = model_normal(anomaly_embedding_copy, embedder)
        recon_feat_top, recon_embeddings_top, loss_b_top = model_normal_top(anomaly_embedding_top_copy,
                                                                            embedder_top)

        up_quantized_recon_t = model.upsample_t(recon_embeddings_top)
        quant_join = torch.cat((up_quantized_recon_t, recon_embeddings), dim=1)
        recon_image_recon = model_decode(quant_join)
        recon_image_recon2 = recon_image_recon
        recon_image_recon2 = np.squeeze(recon_image_recon2.detach().cpu().numpy())
        recon_image_recon2 = np.transpose(recon_image_recon2, (1, 2, 0)) * 255

        # 儲存重建後的圖片
        processed_filename = f"processed_{sample_batched['file_name'][0]}"
        cv2.imwrite(os.path.join('./uploads', processed_filename), np.uint8(recon_image_recon2))

        up_quantized_embedding_t = model.upsample_t(embeddings_t)
        quant_join_real = torch.cat((up_quantized_embedding_t, embeddings), dim=1)
        recon_image = model._decoder_b(quant_join_real)
        recon_image2 = recon_image
        recon_image2 = np.squeeze(recon_image2.detach().cpu().numpy())
        recon_image2 = np.transpose(recon_image2, (1, 2, 0)) * 255

        # 儲存最終處理後的圖片
        final_filename = f"final_{sample_batched['file_name'][0]}"
        cv2.imwrite(os.path.join('./uploads', final_filename), np.uint8(recon_image2))
        
        out_mask = decoder_seg(recon_image_recon.detach(),
                               recon_image.detach())
        out_mask_sm = torch.softmax(out_mask, dim=1)

        # upsampled_mask = model_upsample(recon_image_recon.detach(), recon_image.detach(), out_mask_sm)
        # out_mask_sm_up = torch.softmax(upsampled_mask, dim=1)
        # out_mask_sm_up = crop_image(out_mask_sm_up, img_dim)

        iter += 1

        # out_mask_cv = out_mask_sm_up[0,1,:,:].detach().cpu().numpy()

        out_mask_averaged = torch.nn.functional.avg_pool2d(out_mask_sm[:,1:,:,:], 21, stride=1, padding=21 // 2).cpu().detach().numpy()
        
        a = np.argmax(out_mask_averaged)
        list1.append(a)  
        image_score = np.max(out_mask_averaged)

        total_score.append(image_score)

        flat_true_mask = true_mask_cv.flatten()
        # flat_out_mask = out_mask_cv.flatten()
        # total_pixel_scores[mask_cnt * img_dim * img_dim:(mask_cnt + 1) * img_dim * img_dim] = flat_out_mask
        total_gt_pixel_scores[mask_cnt * img_dim * img_dim:(mask_cnt + 1) * img_dim * img_dim] = flat_true_mask
        mask_cnt += 1
    
    list1 = np.array(list1)

    total_score = np.array(total_score)
    total_gt = np.array(total_gt)
    auroc = roc_auc_score(total_gt, total_score)

    # total_gt_pixel_scores = total_gt_pixel_scores.astype(np.uint8)
    # total_gt_pixel_scores = total_gt_pixel_scores[:img_dim * img_dim * mask_cnt]
    # total_pixel_scores = total_pixel_scores[:img_dim * img_dim * mask_cnt]
    # auroc_pixel = roc_auc_score(total_gt_pixel_scores, total_pixel_scores)
    # ap_pixel = average_precision_score(total_gt_pixel_scores, total_pixel_scores)
    ap = average_precision_score(total_gt, total_score)
    print(total_score, total_gt)
    print(total_gt.shape[0])
    acc = (list1 == total_gt).sum() / total_gt.shape[0]
    print('auroc: ', auroc, ' ap: ', ap, ' acc: ', acc)
    # print(obj_name+" AUC Image: "+str(auroc)+",  AUC Pixel: "+str(auroc_pixel)+", AP Pixel:"+str(ap_pixel)+", AP :"+str(ap))

    return iter

def train_on_device(obj_names, mvtec_path, run_basename):
    auroc_list = []
    # auroc_pixel_list = []
    # ap_pixel_list = []
    ap_list = []
    cnt_total = 0
    
    device = torch.device('cpu')
    
    for obj_name in obj_names:
        print(obj_name)
        run_name_pre = 'vq_model_pretrained_128_4096'

        run_name = run_basename+'_'

        num_hiddens = 128
        num_residual_hiddens = 64
        num_residual_layers = 2
        embedding_dim = 128
        num_embeddings = 4096
        commitment_cost = 0.25
        decay = 0.99
        model_vq = DiscreteLatentModel(num_hiddens, num_residual_layers, num_residual_hiddens,
                      num_embeddings, embedding_dim,
                      commitment_cost, decay)
        model_vq.to(device)
        model_vq.load_state_dict(
            torch.load("./models/" + run_name_pre + ".pckl", map_location=device))
        model_vq.eval()

        sub_res_hi_module = SubspaceRestrictionModule(embedding_size=embedding_dim)
        sub_res_hi_module.load_state_dict(
            torch.load("./models/" + run_name + "subspace_restriction_hi_"+obj_name+".pckl", map_location=device))
        sub_res_hi_module.to(device)
        sub_res_hi_module.eval()

        sub_res_lo_module = SubspaceRestrictionModule(embedding_size=embedding_dim)
        sub_res_lo_module.load_state_dict(
            torch.load("./models/" + run_name + "subspace_restriction_lo_"+obj_name+".pckl", map_location=device))
        sub_res_lo_module.to(device)
        sub_res_lo_module.eval()

        anom_det_module = AnomalyDetectionModule(embedding_size=embedding_dim)
        anom_det_module.load_state_dict(
            torch.load("./models/" + run_name + "anomaly_det_module_"+obj_name+".pckl", map_location=device))
        anom_det_module.to(device)
        anom_det_module.eval()

        image_recon_module = ImageReconstructionNetwork(embedding_dim * 2,
                   num_hiddens,
                   num_residual_layers,
                   num_residual_hiddens)
        image_recon_module.load_state_dict(
            torch.load("./models/" + run_name + "image_recon_module_"+obj_name+".pckl", map_location=device), strict=False)
        image_recon_module.to(device)
        image_recon_module.eval()

        with torch.no_grad():
            cnt = evaluate_model(model_vq, sub_res_hi_module, sub_res_lo_module, image_recon_module, anom_det_module, None, obj_name, mvtec_path, cnt_total)
            cnt_total += cnt
            # ap_list.append(ap)
            # auroc_list.append(auroc)
            # auroc_pixel_list.append(auroc_pixel)
            # ap_pixel_list.append(ap_pixel)

    print(run_basename)
    # auroc_mean = np.mean(auroc_list)
    # auroc_pixel_mean = np.mean(auroc_pixel_list)
    # print("Detection AUROC: "+str(auroc_mean))
    # print("Localization AUROC: "+str(auroc_pixel_mean))
    # print("Localization AP: "+str(np.mean(ap_pixel_list)))

@app.post("/process_image")
async def process_image(file: UploadFile = File(...)):
    try:
        # 讀取上傳的圖片
        contents = await file.read()
        image = Image.open(io.BytesIO(contents))
        image = np.array(image)
        logger.info(f"原始圖片形狀: {image.shape}")
        
        # 創建必要的目錄結構
        upload_dir = './uploads'
        good_dir = os.path.join(upload_dir, 'good')
        os.makedirs(good_dir, exist_ok=True)
        
        # 生成唯一的文件名
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        filename = f"image_{timestamp}_{unique_id}.jpg"
        filepath = os.path.join(good_dir, filename)
        
        # 保存原始圖片到 good 目錄
        cv2.imwrite(filepath, image)
        logger.info(f"成功保存圖片: {filepath}")

        obj_names = ['trajectory']
        mvtec_path = './uploads'

        with torch.no_grad():
            train_on_device(obj_names, mvtec_path, 'DSR')
            
        # 獲取處理後的圖片路徑
        processed_filename = f"processed_{filename}"
        final_filename = f"final_{filename}"
        processed_path = os.path.join(upload_dir, processed_filename)
        final_path = os.path.join(upload_dir, final_filename)
        
        # 檢查處理後的圖片是否存在
        if not os.path.exists(processed_path) or not os.path.exists(final_path):
            raise Exception("處理後的圖片未成功生成")
            
        # 返回圖片的 URL
        base_url = "http://localhost:8000"  # 請根據您的實際部署環境修改
        return {
            "message": "圖片處理完成",
            "images": {
                "original": f"{base_url}/download/{filename}",
                "processed": f"{base_url}/download/{processed_filename}",
                "final": f"{base_url}/download/{final_filename}"
            }
        }

    except Exception as e:
        logger.error(f"處理過程發生錯誤: {str(e)}")
        return {"error": str(e)}

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = os.path.join('./uploads', filename)
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="檔案不存在")
    return FileResponse(file_path, media_type="image/jpeg", filename=filename)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 