import request from '@/services/http';

// 获取证书列表
export const getCertList = (params) => {
  return request({
    url: '/api/v1/cert/list',
    method: 'GET',
    params
  });
};

// 证书续期
export const renewCert = (certId) => {
  return request({
    url: `/api/v1/cert/renew/${certId}`,
    method: 'POST'
  });
};

// 吊销证书
export const revokeCert = (certId) => {
  return request({
    url: `/api/v1/cert/revoke/${certId}`,
    method: 'POST'
  });
};

// 提交CSR申请证书
export const applyCert = (data) => {
  return request({
    url: '/api/v1/cert/apply',
    method: 'POST',
    data
  });
};

