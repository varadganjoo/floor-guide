import test from 'node:test';
import assert from 'node:assert/strict';
import { isSendKey, operationSettled } from '../src/lib/chat-state.ts';

test('IME confirmation and Shift+Enter never send a question', () => {
  assert.equal(isSendKey({key:'Enter',shiftKey:false,isComposing:false,keyCode:13}), true);
  for (const event of [
    {key:'Enter',shiftKey:true,isComposing:false,keyCode:13},
    {key:'Enter',shiftKey:false,isComposing:true,keyCode:13},
    {key:'Enter',shiftKey:false,isComposing:false,keyCode:229},
  ]) assert.equal(isSendKey(event), false);
});
test('a prior completed question does not consume an unsent operation after reload', () => {
  const pending = {conversationId:'chat',path:'/conversations/chat/messages',body:{content:'Question'},previousRunId:'old'};
  assert.equal(operationSettled(pending,{id:'old',status:'completed'}), false);
  assert.equal(operationSettled(pending,{id:'new',status:'completed'}), true);
  assert.equal(operationSettled(pending,{id:'new',status:'awaiting_clarification'}), true);
  assert.equal(operationSettled(pending,{id:'new',status:'failed'}), false);
});
test('clarification retries retain the key until a newer checkpoint or final answer', () => {
  const pending = {conversationId:'chat',path:'/conversations/chat/resume',body:{turn_id:'turn',version:2}};
  assert.equal(operationSettled(pending,{id:'turn',status:'awaiting_clarification',version:2}), false);
  assert.equal(operationSettled(pending,{id:'turn',status:'awaiting_clarification',version:3}), true);
  assert.equal(operationSettled(pending,{id:'turn',status:'completed',version:2}), true);
  assert.equal(operationSettled(pending,{id:'turn',status:'failed',version:3}), false);
});
