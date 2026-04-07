/*
 * SPDX-FileCopyrightText: 2026 Espressif Systems (Shanghai) CO LTD
 *
 * SPDX-License-Identifier: Apache-2.0
 */

#include <cJSON.h>
#include <esp_err.h>
#include <json_to_tlv.h>
#include <lib/core/TLV.h>
#include <tlv_to_json.h>
#include <unity.h>

static constexpr size_t k_tlv_buffer_size = 1024;

static esp_err_t roundtrip_json_tree(const char *input_json, cJSON **output_json)
{
    if (output_json == nullptr) {
        return ESP_ERR_INVALID_ARG;
    }

    *output_json = nullptr;

    uint8_t buffer[k_tlv_buffer_size] = { 0 };
    chip::TLV::TLVWriter writer;
    writer.Init(buffer, sizeof(buffer));

    esp_err_t err = esp_matter::json_to_tlv(input_json, writer, chip::TLV::AnonymousTag());
    if (err != ESP_OK) {
        return err;
    }

    chip::TLV::TLVReader reader;
    reader.Init(buffer, writer.GetLengthWritten());
    return esp_matter::tlv_to_json(reader, output_json);
}

static void expect_roundtrip(const char *input_json, const char *expected_json)
{
    cJSON *actual_json = nullptr;
    cJSON *expected_json_tree = cJSON_Parse(expected_json);
    TEST_ASSERT_NOT_NULL(expected_json_tree);

    esp_err_t err = roundtrip_json_tree(input_json, &actual_json);
    TEST_ASSERT_EQUAL(ESP_OK, err);
    TEST_ASSERT_NOT_NULL(actual_json);

    char *actual_printed = cJSON_PrintUnformatted(actual_json);
    char *expected_printed = cJSON_PrintUnformatted(expected_json_tree);
    TEST_ASSERT_NOT_NULL(actual_printed);
    TEST_ASSERT_NOT_NULL(expected_printed);
    TEST_ASSERT_EQUAL_STRING(expected_printed, actual_printed);

    cJSON_free(actual_printed);
    cJSON_free(expected_printed);
    cJSON_Delete(actual_json);
    cJSON_Delete(expected_json_tree);
}

static void expect_json_to_tlv_failure(const char *input_json)
{
    uint8_t buffer[k_tlv_buffer_size] = { 0 };
    chip::TLV::TLVWriter writer;
    writer.Init(buffer, sizeof(buffer));

    esp_err_t err = esp_matter::json_to_tlv(input_json, writer, chip::TLV::AnonymousTag());
    TEST_ASSERT_TRUE(err != ESP_OK);
}

TEST_CASE("jsontlv roundtrip scalar values", "[jsontlv][roundtrip]")
{
    expect_roundtrip(
        R"({"5:STR":"chip","2:I16":-1234,"4:BOOL":true,"1:U8":42,"3:NULL":null})",
        R"({"1:U8":42,"2:I16":-1234,"3:NULL":null,"4:BOOL":true,"5:STR":"chip"})");

    expect_roundtrip(
        R"({"2:OBJ":{"4:BOOL":false,"1:U8":7},"1:ARR-U8":[3,1,2]})",
        R"({"1:ARR-U8":[3,1,2],"2:OBJ":{"1:U8":7,"4:BOOL":false}})");

    expect_roundtrip(
        R"({"1:BYT":"AQID","2:FP":"INF","3:DFP":"-INF"})",
        R"({"1:BYT":"AQID","2:FP":"INF","3:DFP":"-INF"})");

    expect_roundtrip(
        R"({"1:I64":"-1234567890123456789","2:U64":"12345678901234567890"})",
        R"({"1:I64":"-1234567890123456789","2:U64":"12345678901234567890"})");
}

TEST_CASE("jsontlv roundtrip container and ordering cases", "[jsontlv][roundtrip]")
{
    expect_roundtrip(
        R"({"1:ARR-?":[]})",
        R"({"1:ARR-?":[]})");

    expect_roundtrip(
        R"({"255:U16":65535,"1:U8":1})",
        R"({"1:U8":1,"255:U16":65535})");

    expect_roundtrip(
        R"({"9:OBJ":{"3:STR":"c","1:STR":"a","2:STR":"b"},"2:U8":2,"1:U8":1})",
        R"({"1:U8":1,"2:U8":2,"9:OBJ":{"1:STR":"a","2:STR":"b","3:STR":"c"}})");

    expect_roundtrip(
        R"({"7:ARR-STR":[]})",
        R"({"7:ARR-?":[]})");
}

TEST_CASE("jsontlv roundtrip numeric float values", "[jsontlv][roundtrip]")
{
    cJSON *json = nullptr;
    esp_err_t err = roundtrip_json_tree(R"({"1:FP":1.5,"2:DFP":-2.25})", &json);
    TEST_ASSERT_EQUAL(ESP_OK, err);
    TEST_ASSERT_NOT_NULL(json);

    cJSON *float_value = cJSON_GetObjectItemCaseSensitive(json, "1:FP");
    TEST_ASSERT_NOT_NULL(float_value);
    TEST_ASSERT_TRUE(cJSON_IsNumber(float_value));
    TEST_ASSERT_DOUBLE_WITHIN(0.0001, 1.5, float_value->valuedouble);

    cJSON *double_value = cJSON_GetObjectItemCaseSensitive(json, "2:DFP");
    TEST_ASSERT_NOT_NULL(double_value);
    TEST_ASSERT_TRUE(cJSON_IsNumber(double_value));
    TEST_ASSERT_DOUBLE_WITHIN(0.0001, -2.25, double_value->valuedouble);

    cJSON_Delete(json);
}

TEST_CASE("jsontlv rejects invalid structure and type inputs", "[jsontlv][invalid]")
{
    expect_json_to_tlv_failure(R"({"1:ARR":[1,2,3]})");
    expect_json_to_tlv_failure(R"({"1:BYT":"not-base64"})");
    expect_json_to_tlv_failure(R"({"1":42})");
    expect_json_to_tlv_failure(R"({"1:BOOL":"true"})");
    expect_json_to_tlv_failure(R"({"1:FP":"NaN"})");
    expect_json_to_tlv_failure(R"({"1:I64":"123aaa"})");
    expect_json_to_tlv_failure(R"({"1:I64":"aaa123"})");
    expect_json_to_tlv_failure(R"({"1:U64":"123aaa"})");
    expect_json_to_tlv_failure(R"({"1:U64":"aaa123"})");
}

TEST_CASE("jsontlv rejects invalid numeric boundaries", "[jsontlv][invalid]")
{
    expect_json_to_tlv_failure(R"({"1:U8":256})");
    expect_json_to_tlv_failure(R"({"1:U32":-1})");
    expect_json_to_tlv_failure(R"({"1:I8":128})");
    expect_json_to_tlv_failure(R"({"4294967295:U8":1})");
    expect_json_to_tlv_failure(R"({"1:U32":1.5})");
    expect_json_to_tlv_failure(R"({"1:I32":2147483648})");
}
