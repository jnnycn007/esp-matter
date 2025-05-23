// Copyright 2021 Espressif Systems (Shanghai) CO LTD
//
// Licensed under the Apache License, Version 2.0 (the "License");
// you may not use this file except in compliance with the License.
// You may obtain a copy of the License at
//     http://www.apache.org/licenses/LICENSE-2.0
//
// Unless required by applicable law or agreed to in writing, software
// distributed under the License is distributed on an "AS IS" BASIS,
// WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
// See the License for the specific language governing permissions and
// limitations under the License

#include <esp_log.h>
#include <iot_button.h>

static const char *TAG = "button_driver_hollow";

esp_err_t iot_button_new_gpio_device(const button_config_t *button_config, const button_gpio_config_t *gpio_cfg, button_handle_t *ret_button)
{
    ESP_LOGI(TAG, "Button create");
    *ret_button = NULL;
    return ESP_OK;
}

esp_err_t iot_button_new_adc_device(const button_config_t *button_config, const button_adc_config_t *adc_config, button_handle_t *ret_button)
{
    ESP_LOGI(TAG, "Button create");
    *ret_button = NULL;
    return ESP_OK;
}

esp_err_t iot_button_delete(button_handle_t btn_handle)
{
    ESP_LOGI(TAG, "Button delete");
    return ESP_OK;
}

esp_err_t iot_button_register_cb(button_handle_t btn_handle, button_event_t event, button_event_args_t *event_args, button_cb_t cb, void *usr_data)
{
    ESP_LOGI(TAG, "Button register callback");
    return ESP_OK;
}

esp_err_t iot_button_unregister_cb(button_handle_t btn_handle, button_event_t event, button_event_args_t *event_args)
{
    ESP_LOGI(TAG, "Button unregister callback");
    return ESP_OK;
}

button_event_t iot_button_get_event(button_handle_t btn_handle)
{
    ESP_LOGI(TAG, "Button get event");
    return 0;
}

uint8_t iot_button_get_repeat(button_handle_t btn_handle)
{
    ESP_LOGI(TAG, "Button get repeat");
    return 0;
}
