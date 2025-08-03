import * as assert from 'assert';
import { TimeUtils } from '../../utils/timeUtils';

suite('TimeUtils Test Suite', () => {
  test('formatDuration should format milliseconds correctly', () => {
    assert.strictEqual(TimeUtils.formatDuration(30000), '00:30');
    assert.strictEqual(TimeUtils.formatDuration(90000), '01:30');
    assert.strictEqual(TimeUtils.formatDuration(3661000), '01:01:01');
  });

  test('calculateDuration should compute time differences', () => {
    const start = new Date('2024-01-01T10:00:00Z');
    const end = new Date('2024-01-01T10:01:30Z');
    
    const duration = TimeUtils.calculateDuration(start, end);
    assert.strictEqual(duration, 90000); // 1.5 minutes in ms
  });

  test('getProcessRuntime should format process runtime', () => {
    const startTime = new Date(Date.now() - 90000); // 1.5 minutes ago
    const runtime = TimeUtils.getProcessRuntime(startTime);
    
    assert.ok(runtime.includes(':'));
    assert.ok(runtime.match(/\d{2}:\d{2}/));
  });

  test('parseProcessStartTime should handle various formats', () => {
    const isoDate = '2024-01-01T10:00:00Z';
    const timestamp = '1704110400';
    
    const parsed1 = TimeUtils.parseProcessStartTime(isoDate);
    const parsed2 = TimeUtils.parseProcessStartTime(timestamp);
    
    assert.ok(parsed1 instanceof Date);
    assert.ok(parsed2 instanceof Date);
  });

  test('isWithinLastMinutes should check time ranges', () => {
    const now = new Date();
    const fiveMinutesAgo = new Date(now.getTime() - 5 * 60 * 1000);
    const tenMinutesAgo = new Date(now.getTime() - 10 * 60 * 1000);
    
    assert.ok(TimeUtils.isWithinLastMinutes(fiveMinutesAgo, 7));
    assert.ok(!TimeUtils.isWithinLastMinutes(tenMinutesAgo, 7));
  });

  test('debounce should delay function execution', (done) => {
    let callCount = 0;
    const debouncedFn = TimeUtils.debounce(() => {
      callCount++;
    }, 100);

    debouncedFn();
    debouncedFn();
    debouncedFn();

    // Should not have called yet
    assert.strictEqual(callCount, 0);

    setTimeout(() => {
      // Should have called once after delay
      assert.strictEqual(callCount, 1);
      done();
    }, 150);
  });

  test('throttle should limit function calls', (done) => {
    let callCount = 0;
    const throttledFn = TimeUtils.throttle(() => {
      callCount++;
    }, 100);

    throttledFn();
    throttledFn();
    throttledFn();

    // Should have called once immediately
    assert.strictEqual(callCount, 1);

    setTimeout(() => {
      throttledFn();
      // Should still be one (throttled)
      assert.strictEqual(callCount, 1);
    }, 50);

    setTimeout(() => {
      throttledFn();
      // Should be two after throttle period
      assert.strictEqual(callCount, 2);
      done();
    }, 150);
  });
});