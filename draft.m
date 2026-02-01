clc;clear;close all;
% 1. 指标参数
wp = 3*pi/4; % 通带边界角频率
T = 0.39;    % 过渡点幅值
% 2. 分别设计N=33（奇数，I型）和N=34（偶数，II型）
% 2.1 N=33（奇数，I型线性相位）
N1 = 33;
alpha1 = (N1-1)/2;
k1 = 0:N1-1;
wk1 = 2*pi/N1*k1;
% 构造频率抽样幅值（高通+1个过渡点）
Hrs1 = zeros(1,N1);
% 通带：wk >= wp 或 wk <= 2pi - wp
pass_k1 = find(wk1 >= wp | wk1 <= 2*pi - wp);
Hrs1(pass_k1) = 1;
% 过渡点：通带/阻带交界处
trans_k1 = find(wk1 > 2*pi - wp & wk1 < wp, 1);
Hrs1(trans_k1) = T;
Hrs1(N1 - trans_k1 + 1) = T; % 共轭对称
% 线性相位
angH1 = [-alpha1*wk1(1:alpha1+1), alpha1*(2*pi - wk1(alpha1+2:end))];
H1 = Hrs1 .* exp(1j*angH1);
h1 = real(ifft(H1, N1));
[H1_freq, w1] = freqz(h1, 1, 1000);
mag1 = 20*log10(abs(H1_freq));

% 2.2 N=34（偶数，II型线性相位）
N2 = 34;
alpha2 = (N2-1)/2;
k2 = 0:N2-1;
wk2 = 2*pi/N2*k2;
% 构造频率抽样幅值（高通+1个过渡点）
Hrs2 = zeros(1,N2);
pass_k2 = find(wk2 >= wp | wk2 <= 2*pi - wp);
Hrs2(pass_k2) = 1;
trans_k2 = find(wk2 > 2*pi - wp & wk2 < wp, 1);
Hrs2(trans_k2) = T;
Hrs2(N2 - trans_k2 + 1) = T; % 共轭对称
% 线性相位（II型，偶长度）
angH2 = [-alpha2*wk2];
H2 = Hrs2 .* exp(1j*angH2);
h2 = real(ifft(H2, N2));
[H2_freq, w2] = freqz(h2, 1, 1000);
mag2 = 20*log10(abs(H2_freq));

% 3. 绘图对比
figure;
plot(w1/pi, mag1, 'k-', 'LineWidth',1.2);hold on;
plot(w2/pi, mag2, 'b--', 'LineWidth',1.2);
grid on;
xlabel('\omega/\pi');ylabel('幅度(dB)');
title('N=33和N=34的FIR高通幅频响应');
legend('N=33（奇数/I型）','N=34（偶数/II型）');
ylim([-60, 5]);



function [Hr, W] = Hr_type3(h)
    % Hr_type3：计算III型线性相位FIR滤波器的振幅响应Hr(ω)
    % 输入：h - 滤波器单位冲激响应（奇对称、长度奇数）
    % 输出：Hr - 振幅响应值；W - 频率向量（0~π）
    N = length(h);
    alpha = (N-1)/2;  % 线性相位偏移
    M = 500;          % 频率采样点数（0~π）
    W = linspace(0, pi, M);
    Hr = zeros(1, M);
    
    for i = 1:M
        w = W(i);
        % III型FIR振幅响应公式：Hr(ω) = -2*sum(h(n)*sin((n-α)ω)), n=0~N-1
        sum_val = 0;
        for n = 1:N
            sum_val = sum_val + h(n) * sin((n-1 - alpha)*w);
        end
        Hr(i) = -2 * sum_val;
    end
end