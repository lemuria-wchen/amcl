let argument_types = [
    '研究目的', '研究方法', '研究结果', '研究结论', '其他',
];

let argument_relations = [
    '支持', '反对',
];

let difficulty_types = [
    '简单（基本确定）', '中等（一般确定）', '困难（不确定）'
];

// let difficulty_types = [
//     '简单', '中等', '困难'
// ];

<!-- 插入论点类型 -->
// function insertArgumentType(type_id, content) {
//     let element;
//     if ((type_id + 1) && content) {
//         // 如果 type_id 和 content 都不为空，则插入普通的文本
//         element = '<span>' + argument_types[type_id] + '</span>';
//     } else {
//         // 否则添加 select 多选表单
//         element = '<div class="form-group"><label><select name="arg_type" class="selectpicker show-tick" data-width="auto" required title="Choose one label..">';
//         element += '<optgroup label="Non-argumentative">'
//         for (let tid = 0; tid < 3; tid++) {
//             if ((type_id + 1) && tid === type_id) {
//                 // 如果 type_id 不为空，添加 selected 选项（代表已填答案）
//                 element += '<option value="' + tid + '" selected>' + argument_types[tid] + '</option>';
//             } else {
//                 // 如果 type_id 为空，不添加 selected 选项
//                 element += '<option value="' + tid + '">' + argument_types[tid] + '</option>';
//             }
//         }
//         for (let tid = 4; tid < 5; tid++) {
//             if ((type_id + 1) && tid === type_id) {
//                 // 如果 type_id 不为空，添加 selected 选项（代表已填答案）
//                 element += '<option value="' + tid + '" selected>' + argument_types[tid] + '</option>';
//             } else {
//                 // 如果 type_id 为空，不添加 selected 选项
//                 element += '<option value="' + tid + '">' + argument_types[tid] + '</option>';
//             }
//         }
//         element += '/optgroup';
//         element += '<optgroup label="Argumentative">'
//         for (let tid = 3; tid < 4; tid++) {
//             if ((type_id + 1) && tid === type_id) {
//                 // 如果 type_id 不为空，添加 selected 选项（代表已填答案）
//                 element += '<option value="' + tid + '" selected>' + argument_types[tid] + '</option>';
//             } else {
//                 // 如果 type_id 为空，不添加 selected 选项
//                 element += '<option value="' + tid + '">' + argument_types[tid] + '</option>';
//             }
//         }
//         element += '/optgroup';
//         element += '</select></label></div>';
//     }
//     return $(element)
// }

function insertArgumentType(type_id, content) {
    let element;
    if ((type_id + 1) && content) {
        // 如果 type_id 和 content 都不为空，则插入普通的文本
        element = '<span>' + argument_types[type_id] + '</span>';
    } else {
        // 否则添加 select 多选表单
        element = '<select name="arg_type" class="selectpicker show-tick" required title="Choose one label...">';
        for (let tid = 0; tid < argument_types.length; tid++) {
            if ((type_id + 1) && tid === type_id) {
                // 如果 type_id 不为空，添加 selected 选项（代表已填答案）
                element += '<option value="' + tid + '" selected>' + argument_types[tid] + '</option>';
            } else {
                // 如果 type_id 为空，不添加 selected 选项
                element += '<option value="' + tid + '">' + argument_types[tid] + '</option>';
            }
        }
        element += '</select>';
    }
    return $(element)
}

<!-- 插入 segment -->
function insertSegment(max_segment_id, segment_id, content) {
    let element;
    if ((segment_id + 1) && content) {
        // 如果 segment_id 和 content 都不为空，则插入普通的文本
        element = '<td>' + (segment_id + 1) + '</td>';
    } else {
        // 否则添加 select 多选表单
        element = '<td><select name="arg_rel" class="selectpicker show-tick rel" required title="Choose a sentence...">';
        for (let sid = 0; sid < max_segment_id; sid++) {
            if ((segment_id + 1) && sid === segment_id) {
                // 如果 segment_id 不为空，添加 selected 选项（代表已填答案）
                element += '<option value="' + sid + '" selected>Segment_' + (sid + 1) + '</option>';
            } else {
                // 如果 segment_id 为空，不添加 selected 选项
                element += '<option value="' + sid + '">Segment_' + (sid + 1) + '</option>';
            }
        }
        element += '</select></td>';
    }
    return $(element)
}

<!-- 插入 relation -->
function insertRelation(relation_id, content) {
    let element;
    if ((relation_id + 1) && content) {
        // 如果 relation_id 和 content 都不为空，则插入普通的文本
        element = '<td>' + argument_relations[relation_id] + '</td>';
    } else {
        // 否则添加 select 多选表单
        element = '<td><select name="arg_rel" class="selectpicker show-tick rel" required>';
        for (let rid = 0; rid < argument_relations.length; rid++) {
            if ((relation_id + 1) && rid === relation_id) {
                // 如果 relation_id 不为空，添加 selected 选项（代表已填答案）
                element += '<option value="' + rid + '" selected>' + argument_relations[rid] + '</option>';
            } else {
                // 如果 relation_id 为空，不添加 selected 选项
                element += '<option value="' + rid + '">' + argument_relations[rid] + '</option>';
            }
        }
        element += '</select></td>';
    }
    return $(element)
}

<!-- 插入删除按钮 -->
function insertDeleteButton() {
    return $('<td><button class="btn btn-danger">Delete</button></td>'
    ).bind('click', function () {
        $(this).parent().remove()
    })
}

<!-- 插入关系行 -->
function insertArgumentRelation(max_segment_id, default_values, content, tr_class) {
    let tr = '';
    if (tr_class) {
        tr = $('<tr>');
    } else {
        tr = $('<tr class="arg_rel">');
    }
    if (default_values) {
        tr.append(insertSegment(max_segment_id, default_values[0], content));
        tr.append(insertRelation(default_values[1], content));
        tr.append(insertSegment(max_segment_id, default_values[2], content));
    } else {
        tr.append(insertSegment(max_segment_id));
        tr.append(insertRelation());
        tr.append(insertSegment(max_segment_id));
    }
    if (!content) {
        tr.append(insertDeleteButton());
    }
    return tr;
}

<!-- 插入论点类型 -->
function insertDifficulty(difficulty_id, content) {
    let element = '';
    if ((difficulty_id + 1) && content) {
        element = '<span>' + difficulty_types[difficulty_id] + '</span>';
    } else {
        if (difficulty_id + 1) {
            for (let did = 0; did < difficulty_types.length; did++) {
                if (did === difficulty_id) {
                    element += '<label class="radio-inline" style="margin: 0 0 0 2%;"><input type="radio" name="diff" value="' + did + '" required checked>'
                        + difficulty_types[did] + '</label>';
                } else {
                    element += '<label class="radio-inline" style="margin: 0 0 0 2%;"><input type="radio" name="diff" value="' + did + '" required>'
                        + difficulty_types[did] + '</label>';
                }
            }
        } else {
            for (let did = 0; did < difficulty_types.length; did++) {
                element += '<label class="radio-inline" style="margin: 0 0 0 2%;"><input type="radio" name="diff" value="' + did + '" required>'
                    + difficulty_types[did] + '</label>';
            }
        }
    }
    return $(element)
}
